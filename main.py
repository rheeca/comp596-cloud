import pymysql
import sqlalchemy

from flask import Flask, render_template, request
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import (Table, MetaData, Column, Integer, String)


app = Flask(__name__)

DB_HOST = ''
DB_USER = ''
DB_PASS = ''
DB_NAME = ''
DB_PORT = '3306'
TABLE_NAME = ''
CONNECTION_NAME = '' # Format: 'project_id:region:instance_name'

@app.route("/", methods=['GET', 'POST'])
def root():
    if request.method == 'POST':
        # Get data from the form
        id = request.form['id']
        name = request.form['name']
    
        # Insert to Cloud SQL database
        engine = connect_with_connector()
        metadata = MetaData()

        table = Table(
        TABLE_NAME, metadata, 
            Column('id', Integer, primary_key = True), 
            Column('name', String()),
        )
        metadata.create_all(engine)
            
        with engine.connect() as conn:
            stmt = table.insert().values(id=id, name=name)
            result = conn.execute(stmt)
            conn.commit()

    return render_template('index.html')

def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """Initializes a connection pool for a Cloud SQL instance of MySQL."""
    ip_type = IPTypes.PUBLIC

    connector = Connector(ip_type)

    def getconn() -> pymysql.connections.Connection:
        conn: pymysql.connections.Connection = connector.connect(
            CONNECTION_NAME,
            "pymysql",
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
        )
        return conn

    engine = sqlalchemy.create_engine(
        # Equivalent URL:
        # mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
        sqlalchemy.engine.url.URL.create(
            drivername="mysql+pymysql",
            username=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
        ),
        creator=getconn,
        echo=True,
    )
    
    return engine


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
