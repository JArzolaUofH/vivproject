import flask
from flask import jsonify, request, redirect, url_for, send_from_directory, render_template, session
from werkzeug.security import check_password_hash
from sql import create_connection
from sql import execute_read_query
from sql import execute_query
import creds
import os
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime



frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')    

# setting up an application name
app = flask.Flask(__name__,template_folder=frontend_dir) # sets up the app
app.secret_key = 'bhu87ygvBHU*&YGV'
app.config["DEBUG"] = True # allow to show errors in browser


##############################################################
############ Email Function #################################
#############################################################
def send_email(subject, sender_email, recipient_email, smtp_password, content):
    # Create a multipart message
    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    # set content
    msg.set_content(content)


    # Add message body
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, smtp_password)

        smtp.send_message(msg)


#send_email(subject, sender_email, recipient_email, smtp_password)



###############################################
############# CLIENT TABLE APIs ######################
#################################################

# APIs for client tables
# THIS API READS ALL CLIENTS
@app.route('/api/clientall', methods=['GET'])
def api_read_clientall():
    # this api reads all clients
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    sql = "SELECT * FROM codeIncDB.client"
    clients = execute_read_query(conn, sql)
    
    # Render HTML template and pass client data to it
    # return render_template('client_all.html', clients=clients)
    return jsonify(clients)


# THIS API WILL READ ONLY ONE CLIENT
# AN ID MUST BE PROVIDED TO READ THAT CLIENT'S INFO
@app.route('/api/client', methods=['GET'])
def api_read_client():
    # collects data from user to read an entry
    print(request.args)
    if 'id' in request.args: # only if an id is provided as an arg, proceed
        id = int(request.args['id'])
    else:
        return 'ERROR: no id provided'
    # connects to database to run the SQL statement
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    sql = "SELECT * FROM client"
    client = execute_read_query(conn, sql)
    print(client)
    results = []
    print(results)
    for c in client:
        if c['client_id'] == id:
            results.append(c)
    # if no results to return, send message to try a new ID.
    if len(results) == 0:
        return "ID not found. Try a different ID."
    # returns client data in json format
    return jsonify(results)


#  API TO ADD NEW CLIENT
@app.route('/api/addclient', methods=['POST'])
def addclient():
    conn = None
    cursor = None  # Initialize cursor outside the try-except block
    
    try:
        # Collect client data from request JSON
        request_data = request.get_json()
        print(request_data)
        newfname = request_data['fname']
        newlname = request_data['lname']
        newphonenum = request_data['phone_number']
        newemail = request_data['email_address']
        new_medical_history = request_data.get('medical_history')
        new_skincare_products = request_data.get('skincare_products')
        new_pmu_done = request_data.get('pmu_done')
        new_over_18 = request_data.get('over_18')
        new_submission_date = request_data.get('submission_date', datetime.today().strftime('%Y-%m-%d'))
        newstatus = request_data.get('status_id', 1)
        newnotes = request_data.get('notes', None)
        newwaiver = request_data.get('waiver_signed', False)
        newdeposit = request_data.get('deposit_paid', 2)
        newservice = request_data.get('service_id')

        # setting service name for email
        serviceName = ''
        if newservice == 3:
            serviceName = 'Touch Up'
        elif newservice == 4:
            serviceName = 'Initial Consul'
        else:
            serviceName = 'Correction'

        try:    
            #setting email content
            content = f'''
            Hello,\n
            You have a new client!
            {newfname} {newlname} has registered!
            Phone Number: {newphonenum}
            Email: {newemail}
            Medical History: {new_medical_history}
            Skincare Products: {new_skincare_products}
            PMU: {new_pmu_done}
            Over 18: {new_over_18}
            Notes: {newnotes}
            Service Requested: {serviceName}
                        '''

            send_email('Test', sender_email, recipient_email, smtp_password, content)
        except:
            print('email cannot be sent')
         
        # Connect to the database
        mycreds = creds.Creds()
        conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
        cursor = conn.cursor()
        
        # SQL statement with parameterized query
        create_statement = '''INSERT INTO codeIncDB.client (fname, 
                                                            lname, 
                                                            phone_number, 
                                                            email_address, 
                                                            medical_history, 
                                                            skincare_products, 
                                                            pmu_done, 
                                                            over_18, 
                                                            submission_date,
                                                            notes,
                                                            service_id,
                                                            status_id,
                                                            deposit_paid,
                                                            waiver_signed
                                                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        
        # Execute the query with parameters
        cursor.execute(create_statement, (newfname, newlname, 
                                          newphonenum, newemail, 
                                          new_medical_history, new_skincare_products, 
                                          new_pmu_done, new_over_18, 
                                          new_submission_date, newnotes,
                                          newservice, newstatus,
                                          newdeposit, newwaiver))

        
        # Commit the transaction
        conn.commit()
        
        # Return success message
        return jsonify({'message': 'add request successful'}), 201
    except Exception as e:
        # Rollback the transaction in case of error
        if conn:
            conn.rollback()
        # Close cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        # Return error message
        return jsonify({'error': str(e)}), 400
    finally:
        # Close cursor and connection in case of success or error
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Route for the next step after form submission
@app.route('/next-step')
def next_step():
    return jsonify({'next_step': 'load_next_form'}), 200

# delete a client
@app.route('/api/client', methods=['DELETE'])
def api_delete_client():
    # print(request.args)
    # collects data from user to delete an entry
    # request_data = request.get_json()
    # print(request_data)

    request_data = request.get_json()
    id_to_delete = request_data['id']
    # connects to database to run the SQL statement
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    sql = "DELETE FROM client WHERE client_id = %s" % id_to_delete

    execute_query(conn, sql)
    return "delete was successful"


@app.route('/api/update_client', methods=['PUT'])
def update_client():

    data = request.get_json()
    client_id = data['client_id']
    column = data['column']
    newValue = data.get('newValue')
    print(data)
    # client_id = data['client_id']
    # fname = data.get('fname')
    # lname = data.get('lname')
    # phone_number = data.get('phone_number')
    # email_address = data.get('email_address')
    # medical_history = data.get('medical_history')
    # skincare_products = data.get('skincare_products')
    # pmu_done = data.get('pmu_done')
    # over_18 = data.get('over_18')
    # waiver_signed = data.get('waiver_signed')
    # deposit_paid = data.get('deposit_paid')
    # notes = data.get('notes')
    # submission_date = data.get('submission_date')
    # client_status = data.get('statusSelect')

    # cursor = mydb.cursor()
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    # sql = "UPDATE client SET "
    params = []

    # if fname is not None:
    #     sql += f"fname = '{fname}', "
    #     params.append(fname)
    # if lname is not None:
    #     sql += f"lname = '{lname}', "
    #     params.append(lname)
    # if client_status is not None:
    #     sql += f"status_id = '{client_status}', "
    #     params.append(client_status)
    # if phone_number is not None:
    #     sql += f"phone_number = {phone_number}, "
    #     params.append(phone_number)
    # if email_address is not None:
    #     sql += f"email_address = '{email_address}', "
    #     params.append(email_address)
    # if medical_history is not None:
    #     sql += f"medical_history = '{medical_history}', "
    #     params.append(medical_history)
    # if skincare_products is not None:
    #     sql += f"skincare_products = '{skincare_products}', "
    #     params.append(skincare_products)
    # if pmu_done is not None:
    #     sql += f"pmu_done = '{pmu_done}', "
    #     params.append(pmu_done)
    # if over_18 is not None:
    #     sql += f"over_18 = {over_18}, "
    #     params.append(over_18)
    # if submission_date is not None:
    #     sql += f"submission_date = {submission_date}, "
    #     params.append(submission_date)
    # if waiver_signed is not None:
    #     sql += f"waiver_signed = {waiver_signed}, "
    #     params.append(waiver_signed)
    # if deposit_paid is not None:
    #     sql += f"deposit_paid = {deposit_paid}, "
    #     params.append(deposit_paid)
    # if notes is not None:
    #     sql += f'''notes = "{notes}", '''
    #     params.append(notes)

    # Remove the trailing comma and space
    # sql = sql[:-2]

    # sql += f" WHERE client_id = {client_id};"
    if isinstance(newValue, str):
        sql = f'''UPDATE client set {column} = "{newValue}" WHERE client_id = {client_id}'''
    else:
        sql = f"UPDATE client set {column} = {newValue} WHERE client_id = {client_id}"
    # params.append(client_id)

    print(sql)
    execute_query(conn, sql)
    return jsonify({'message': 'Client updated successfully'})




###############################################
############# FORM TABLE APIs ######################
#################################################

# api to read ALL forms
@app.route('/api/formall', methods=['GET'])
def api_read_formall():
    # this api reads all forms
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    sql = "SELECT * FROM form"
    clients = execute_read_query(conn, sql)
    # returns client data in json format
    return jsonify(clients)

#  API TO ADD NEW form
@app.route('/api/addform', methods=['POST'])
def addform():
    # Collect form data from the request
    request_data = request.get_json()
    newmedhistory = request_data['medicalHistory']
    newskinprods = request_data['skincareProducts']
    newpmu = request_data['pmuDone']
    new18 = 1 if request_data.get('over18') else 0

    # Connect to database and execute SQL statement
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    create_statement = """INSERT INTO form (medical_history, skincare_products, pmu_done, over_18)
                          VALUES ('%s', '%s', '%s', %s)""" % (newmedhistory, newskinprods, newpmu, new18)
    execute_query(conn, create_statement)

    return jsonify({"message": "add request successful"})



###############################################
############# Service TABLE APIs ######################
#################################################

# THIS API READS ALL SERVICES
@app.route('/api/servicesall', methods=['GET'])
def api_read_servicesall():
    # this api reads all services
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    sql = "SELECT * FROM service"
    services = execute_read_query(conn, sql)
    # returns client data in json format
    return jsonify(services)
     # Render HTML template and pass client data to it
    #return render_template('index.html', services=services)

#  API TO ADD NEW SERVICE
@app.route('/api/addservice', methods=['POST'])
def addservice():
    # collects service data from user to add a new service to the table
    request_data = request.get_json()
    newservice = request_data['service_name']
    newprice = request_data['service_price']
    newinfo = request_data['service_info']
    # connects to database to run the SQL statement
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    create_statement = "INSERT INTO service (service_name, service_price, service_info) VALUES ('%s', %s, '%s')" % (newservice, newprice, newinfo)
    execute_query(conn, create_statement)
    return "add request successful"

# delete a service
@app.route('/api/service', methods=['DELETE'])
def api_delete_service():    
    request_data = request.get_json()
    id_to_delete = request_data['id']
    # connects to database to run the SQL statement
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    sql = "DELETE FROM service WHERE service_id = %s" % id_to_delete

    execute_query(conn, sql)
    return "delete was successful"


###############################################
############# APPOINTMENT TABLE APIs ######################
#################################################

@app.route('/')
def api_read_servicesall2():
    # this api reads all services
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    sql = "SELECT * FROM service"
    services = execute_read_query(conn, sql)
    # returns client data in json format
    # return jsonify(services)
     # Render HTML template and pass client data to it
    print(services)
    return render_template('index.html', services=services)


def serve_frontend():
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(frontend_dir, filename)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Database query and validation logic (replace with your actual logic)
        if username == 'admin' and password == 'admin':  # Assuming hashed password
            session['logged_in'] = True  # Set session variable for login status
            return redirect(url_for('login_success'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')  # For GET requests

@app.route('/login_success')
def login_success():
    if 'logged_in' in session and session['logged_in']:  # Check if user is logged in
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))  # Redirect to login if not logged in

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Remove login session variable
    return redirect(url_for('login'))  # Redirect to login after logout

@app.route('/query', methods=['POST'])
def query():
    # id = request.form['id']
    phone_number = request.form['phone_number']
    mycreds = creds.Creds()
    conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
    query = '''select client.client_id,
                    concat(client.fname," ",client.lname) as "Client Name", 
                    client.phone_number as "Phone Number", 
                    client.email_address as "Email", 
                    service.service_name as "Service", 
                    client.medical_history as "Medical History", 
                    client.skincare_products as "Skincare Products",
                    client.pmu_done as "PMU Done",
                    CASE client.over_18
                    when 1 then 'Yes'
                    else 'No'
                    END as "Over 18",
					CASE client.waiver_signed
					WHEN 1 THEN 'Complete'
					ELSE 'Incomplete'
					END AS 'Waiver Signed',
                    deposit_paid.deposit_status as "Deposit",
                    client.notes as "Notes",
                    client_status.status_name as "Client Status"
                from client
                join service on client.service_id = service.service_id
                join deposit_paid on client.deposit_paid = deposit_paid.deposit_id
                join client_status on client.status_id = client_status.status_id
                where client.phone_number = %s;''' % phone_number 
                # where client.client_id = %s;''' % id 
    queryResult = execute_read_query(conn, query)
    print(queryResult)
    # return render_template('reports.html', queryResult=queryResult)
    return jsonify(queryResult=queryResult)


@app.route('/search') 
def search(): 
    if 'logged_in' in session and session['logged_in']:
        mycreds = creds.Creds()
        conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)

        query = '''select client.client_id,
                        concat(client.fname," ",client.lname) as "Client Name", 
                        client.phone_number as "Phone Number", 
                        client.email_address as "Email", 
                        service.service_name as "Service", 
                        client.medical_history as "Medical History", 
                        client.skincare_products as "Skincare Products",
                        client.pmu_done as "PMU Done",
                        CASE client.over_18
                        when 1 then 'Yes'
                        else 'No'
                        END as "Over 18",
                        CASE client.waiver_signed
                        WHEN 1 THEN 'Complete'
                        ELSE 'Incomplete'
                        END AS 'Waiver Signed',
                        deposit_paid.deposit_status as "Deposit",
                        client.notes as "Notes",
                        client_status.status_name as "Client Status"
                    from client
                    join service on client.service_id = service.service_id
                    join deposit_paid on client.deposit_paid = deposit_paid.deposit_id
                    join client_status on client.status_id = client_status.status_id
                    order by client.client_id;'''
        queryResult = execute_read_query(conn, query)

        colNamessql = '''SELECT COLUMN_NAME
                        FROM information_schema.columns
                        WHERE TABLE_SCHEMA = 'codeIncDB'
                        AND TABLE_NAME = 'client';'''
        colNames = execute_read_query(conn, colNamessql)

        client_status_query = f"SELECT * FROM client_status;"
        client_status_result = execute_read_query(conn, client_status_query)
        print(client_status_result)

        deposit_paid_query = f"SELECT * FROM deposit_paid;"
        deposit_paid_result = execute_read_query(conn, deposit_paid_query)
        print(deposit_paid_result)

        # returns all clients
        sql2 = "SELECT * FROM codeIncDB.client"
        clients = execute_read_query(conn, sql2)

        sql = "SELECT * FROM service"
        services = execute_read_query(conn, sql)

        searchcolsql = '''SELECT COLUMN_NAME
                            FROM information_schema.columns
                            WHERE TABLE_SCHEMA = 'codeIncDB'
                            AND TABLE_NAME = 'client'
                            and column_name not in ('client_id', 
                            'medical_history', 'skincare_products', 
                            'pmu_done', 'over_18', 'waiver_signed', 
                            'deposit_paid', 'notes', 'submission_date');'''
        searchcol = execute_read_query(conn, searchcolsql)

        return render_template("search.html",   colNames=colNames,
                                                clients=clients, 
                                                services=services,
                                                deposit_paid_result=deposit_paid_result,
                                                client_status_result=client_status_result,
                                                searchcol=searchcol,
                                                queryResult=queryResult
                                                )
    else:
        return redirect(url_for('login'))

@app.route('/reports')
def report1():
    if 'logged_in' in session and session['logged_in']:  # Check if user is logged in
        mycreds = creds.Creds()
        conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
        sql = "SELECT * FROM service"
        services = execute_read_query(conn, sql)

    # returns all clients
        sql2 = "SELECT * FROM codeIncDB.client"
        clients = execute_read_query(conn, sql2)

    # returns all clients with booked appointment
        scheduledClientssql = '''select client.fname,
                                client.lname,
                                client.email_address,
                                client.phone_number,
                                client_status.status_name,
                                service.service_name
                                from client join client_status on client.status_id = client_status.status_id
                                join service on client.service_id = service.service_id
                                where client_status.status_name = 'Scheduled';'''
    
        scheduledClients = execute_read_query(conn, scheduledClientssql)

    # 10 most recent clients who haven't scheduled an appt
        tenclientssql = '''select concat(fname," ",lname) as "Client_Name", phone_number, email_address, service.service_name as "Service"
                        from client
                        inner join service on client.service_id = service.service_id
                        where status_id not in (2,3,4)
                        order by submission_date desc
                        limit 10;'''
    
        tenclients = execute_read_query(conn, tenclientssql)
    # print(tenclients)

  #  Value of scheduled Clients
        scheduledValuesql =    '''select sum(service.service_price) as 'Scheduled_Value' from client
        join service on client.service_id = service.service_id
        join client_status on client.status_id = client_status.status_id
        where client_status.status_name = 'Scheduled';'''
        scheduledValue = execute_read_query(conn, scheduledValuesql)

        revenueByYearSQL = '''SELECT 
                                    CASE WHEN Year(client.submission_date) IS NULL THEN 'Total' ELSE Year(client.submission_date) END AS 'Year', 
                                    SUM(service.service_price) AS 'Revenue'
                                FROM 
                                    client
                                RIGHT JOIN 
                                    service ON client.service_id = service.service_id
                                WHERE 
                                    client.status_id = 3
                                GROUP BY 
                                    year(client.submission_date) WITH ROLLUP
                                    
                                order by year(client.submission_date) desc;'''
        revenuebyyear = execute_read_query(conn, revenueByYearSQL)

        revenuebyserviceSQL = '''SELECT 
                CASE WHEN service.service_name IS NULL THEN 'Total' ELSE service.service_name END AS 'Service', 
                    SUM(service.service_price) AS 'Revenue'
                FROM 
                    client
                RIGHT JOIN 
                    service ON client.service_id = service.service_id
                WHERE 
                    client.status_id = 3
                GROUP BY 
                    service.service_name WITH ROLLUP;'''
        revenuebyservice = execute_read_query(conn, revenuebyserviceSQL)

        servicesOverTimesql = '''SELECT 
                                service.service_name 'Service',
                                COUNT(client.service_id) AS "All_Time",
                                SUM(CASE WHEN EXTRACT(YEAR FROM client.submission_date) = 2022 THEN 1 ELSE 0 END) AS "twentytwo",
                                SUM(CASE WHEN EXTRACT(YEAR FROM client.submission_date) = 2023 THEN 1 ELSE 0 END) AS "twentythree",
                                SUM(CASE WHEN EXTRACT(YEAR FROM client.submission_date) = 2024 THEN 1 ELSE 0 END) AS "twentyfour"
                            FROM 
                                client
                            JOIN 
                                service ON client.service_id = service.service_id
                            GROUP BY 
                                client.service_id, service.service_name;'''
        servicesOverTime = execute_read_query(conn, servicesOverTimesql)

    # def columnNames():
#     mycreds = creds.Creds()
#     conn = create_connection(mycreds.conString, mycreds.userName, mycreds.password, mycreds.dbName)
        colNamessql = '''SELECT COLUMN_NAME
                    FROM information_schema.columns
                    WHERE TABLE_SCHEMA = 'codeIncDB'
                    AND TABLE_NAME = 'client';'''
        colNames = execute_read_query(conn, colNamessql)
    # return jsonify(colNames) 

        client_status_query = f"SELECT * FROM client_status;"
        client_status_result = execute_read_query(conn, client_status_query)
        print(client_status_result)

        deposit_paid_query = f"SELECT * FROM deposit_paid;"
        deposit_paid_result = execute_read_query(conn, deposit_paid_query)
        print(deposit_paid_result)

        print(services)



        return render_template("reports.html", services=services,
                                                colNames=colNames,
                                                revenuebyservice=revenuebyservice,
                                                clients=clients, 
                                                scheduledClients=scheduledClients,
                                                tenclients = tenclients,
                                                scheduledValue=scheduledValue,
                                                revenuebyyear=revenuebyyear,
                                                servicesOverTime=servicesOverTime,
                                                client_status_result=client_status_result,
                                                deposit_paid_result=deposit_paid_result
                                                )

    else:
            return redirect(url_for('login'))

app.run()
