# Health State Tracking

A handy web app for tracking and managing within a mid-sized organization (~ hundreds of people).

Made public in memory of COVID-19, and in hopes that it may never be needed again.

## Usage

1. Clone this repo
2. Install dependencies: `pip3 install -r requirements.txt`
3. Create `people.csv`, `tracking.csv`, `users.csv` in `data` folder
   - `people.csv`:
     ```csv
     部门,姓名,用工形式,联系电话,备注
     ```
   - `tracking.csv`:
     ```csv
     日期,填报时间,部门,姓名,用工形式,联系电话,核酸,抗原,健康码,疫苗,体温,体温异常,目前状态,健康状态
     ```
   - `users.csv`:
     ```csv
     name,pass
     ```
4. Create `secrets.toml` in `.streamlit` folder
   - `secrets.toml`:
     ```toml
     [su]
     admin = '12345678900'
     [visitor]
     public = '98765432100'
     [viewer]
     visitor = '123456'
     [salt]
     salt1 = 'salt1'
     salt2 = 'salt2'
     ```
5. Run `streamlit run Tracking.py` and open the link in browser
