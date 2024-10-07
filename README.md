## Building a Conversational AI Chatbot using locally installed LLM and Oracle Database for Real-Time Insights


In today's rapidly evolving tech landscape, leveraging AI to make data more accessible has become a game changer for organizations. However, practical guides to connect large language models (LLMs) with enterprise databases, particularly for Oracle on prem environments, are surprisingly scarce. This blog post aims to bridge that gap by showing you how to integrate Langchain with an Oracle Database to create a chatbot capable of translating complex database queries into human-friendly responses. Whether you are a seasoned developer or just exploring AI for business intelligence, this step-by-step guide will help you build a powerful interface for your Oracle data, allowing users to interact naturally and get insightful responses directly from your database.



1. Create linux users for this setup.
2. Install Oracle Instant Client
3. Configure tnsnames.ora
4. Install Oracle 23ai Free database
5. Test sqlplus connectivity to oracle database using installed instant client.
6. Install and activiate python virtual environment.
7. Install required python packages using pip
8. Install ollama locally on linux.
9. Download llm model (llama3.2) using ollama.
10. Assemble the python script and test cli
13. Run chatbot with streamlit
14. As chatbot questions about database.


### Step 1: Create Linux users for the this setup (Optional: as root )
```
sudo useradd -m devopsuser
sudo passwd devopsuser
```

### Step 2: Install Oracle Instant Client on Fedora (as root)

```
Update the package list
sudo dnf update -y

# Install required dependencies
sudo dnf install -y libaio

# Download Oracle Instant Client from the official Oracle website
(https://www.oracle.com/database/technologies/instant-client.html)
You will require and login to oracle portal to get the client.

# Copy the downloaded clients to the linux system and Unzip the downloaded file
unzip instantclient*.zip -d /opt/oracle
#or
rpm -iUvh oracleinstant-client.rpm
```

This will install oracle libraries and binaries to /usr/lib/oracle/<VERSION>/client64/ we need create tnsnames.ora for Orale database service discover with tns.


### 3 Configure tnsnames.ora for oracle db service discovery  (as root)
```
cd /usr/lib/oracle/<VERSION>/client64/
mkdir -p network/admin
cd network/admin
touch tnsnames.ora
```

Add the below entry to your tnsnames.ora file

```
# Don't forget to adjust SID and IP string.
FREE=
        (DESCRIPTION=
                (ADDRESS=(PROTOCOL=tcp)(HOST=<YOUR_DATABASE_IP>)(PORT=1521))
            (CONNECT_DATA=
                (SERVICE_NAME=FREEPDB1)
                (INSTANCE_NAME=FREE)
            )
        )

```

### 4. Download and install oracle database 23ai free version (Optional as root)

Dowload oracle rpms onto the Linux machine from https://www.oracle.com/database/free/get-started/

```
wget https://yum.oracle.com/repo/OracleLinux/OL9/appstream/x86_64/getPackage/oracle-database-preinstall-23ai-1.0-2.el9.x86_64.rpm
wget https://download.oracle.com/otn-pub/otn_software/db-free/oracle-database-free-23ai-1.0-1.el9.x86_64.rpm

dnf install -y oracle-database-preinstall-23ai-1.0-2.el9.x86_64.rpm
dnf install -y oracle-database-free-23ai-1.0-1.el9.x86_64.rpm

#Once the download is completed, initiate the configuration
/etc/init.d/oracle-free-23ai configure

# Once configuration is done, start the databse
/etc/init.d/oracle-free-23ai start

# Setup oracle home and sid for root so that we can connect and import the sample schemas

echo "
export ORACLE_HOME=/opt/oracle/product/23ai/dbhomeFree
export ORACLE_SID=FREE

PATH=$PATH:$ORACLE_HOME/bin
" >> ~/.bash_profile

```


Download sample data and load to the database for later usage with llm. (Optional, as root)

```
wget https://github.com/oracle-samples/db-sample-schemas/archive/refs/tags/v23.3.zip
unzip v23.3.zip
cd db-sample-schemas-23.3
cd human_resources
sqlplus sys@localhost:1521/FREEPDB1 as sysdba
# We are creating and install sales history schema as sh
@hr_install.sql
```

You should see the creation summary as below:

![image](https://github.com/user-attachments/assets/270a9963-c7aa-40f0-a4b6-cd4113eab12d)





Switch to devopsuser user and lets test the sqlplus connectivity. (as devopsuser)
```
# Set up environment variables in .bash_profile
su -l devopsuser
echo "export ORACLE_HOME=/usr/lib/oracle/<VERSION>/client64" >> ~/.bash_profile
echo "export PATH=$ORACLE_HOME/bin:$PATH" >> ~/.bash_profile
echo "export LD_LIBRARY_PATH=$ORACLE_HOME" >> ~/.bash_profile

source ~/.bash_profile

```
Connect to the 23ai database as sales history user sh/<password>

```
sqlplus hr/hr@FREE
```

![image](https://github.com/user-attachments/assets/e75808a8-f2cf-43c2-b3e9-603d88031cfd)



### Install and activiate python virtual environment (as devops)

Without virtual env for python, you will be installing all python packages on host system which is not desirable. 
Check the deatils on how to install python venv at : https://docs.python.org/3/library/venv.html

```
python -m venv oracle-llm
source oracle-llm/bin/activate
# To ensure pip is available to install python packages in next steps.
which pip
```

![image](https://github.com/user-attachments/assets/2ffccc1d-6d5d-474b-8a8e-592b53cdd03e)




### Install required python packages using pip (as devops)

```
mkdir oracle-llm-demo
cd oracle-llm-demo

echo "
langchain==0.3.2
langchain_community==0.3.1
langchain_core==0.3.8
ollama==0.3.3
python-dotenv==1.0.1
spacy==3.8.2
SQLAlchemy==2.0.35
streamlit==1.39.0
" > requirements.txt

pip install -r requirements.txt

```
![image](https://github.com/user-attachments/assets/a5a3a8b7-222c-484e-980c-8076cc7a70da)



### Install ollama locally on linux. (as root user)

```
curl -fsSL https://ollama.com/install.sh | sh
```

###  Download llm model (llama3.2) using ollama. (as root user)

![image](https://github.com/user-attachments/assets/18527d78-6db1-4dc5-9879-2645ce5488c1)



### Python script execution:


![image](https://github.com/user-attachments/assets/6b716cbd-9cf4-4935-ac33-00ba6c06a299)





I hope these steps have been useful to you in your attempt to configure and task to an Oracle database using an LLM -- thanks!
