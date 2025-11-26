# agritradewatch- Github Repo for https://mandigo.in
MandiGo "Agri Market Price Watch: A real-time GIS-based comprehensive market decision support system for all agricultural stakeholders, including farmers, producers, consumers, wholesalers, and retailers" is a project sponsored by the Technology Innovation Hub for translational research on IoT (Internet-of-Things) and IoE (Internet-of-Everything) under Grants TIH-IoT-2025. IITB IRCC Project Code RD/0125-TIHIR18-007.

MandiGo is a data-driven platform that empowers farmers and consumers to make informed selling/buying decisions by accessing historical and real-time crop/commodities prices. By crowdsourcing data directly from all stakeholders in the supply chain, including data from sources like AgMark, e-NAM, the tool offers market-level insights on commodity prices.

**Purpose of MandiGo**

MandiGo is committed to ensuring price transparency, the first step in enabling farmers to sell their commodities at fair prices while reducing exploitation in the supply chain. We believe that farmers should have the right to decide their selling price, and MandiGo stands as a platform that empowers them with information, choice, and control over their economic decisions through historical and real-time price awareness in an area of interest.

**What are we offering?**


MandiGo offers a user-friendly web platform and mobile app to collect and visualise real-time georeferenced commodity (such as vegetables, fruits, cereals, pulses, etc.) price information through crowdsourcing. By using the app, stakeholders can:

    1. Compare commodity prices across nearby mandis and markets.
    2. Select the optimal timing and location for selling or buying commodities.
    3. Stakeholders, mainly, can put their produce/commodities for sale

👦 You will need python3 and pip3 for installing packages

👶 fork the repo

👨 clone your repo locally

👴 install postgresql

sudo apt-get install postgresql

🙈 create virtual env

pip3 -m venv VIRTUALENVNAME 

🙉 activate virtual env

source VIRTUALENVNAME/bin/activate

🙊 install dependencies

pip3 install -r requirments.txt
or
pip3 install django psycopg2 social-auth-app-django

💀 setup database using postgres-setup.txt

🙏 email at nautiyalanimesh@gmail.com for asking keys for projects

👏 create tables

python3 manage.py migrate

🤡create superuser

python3 manage.py createsuperuser

🎉 run at http://127.0.0.1:8000/

python3 manage.py runserver
