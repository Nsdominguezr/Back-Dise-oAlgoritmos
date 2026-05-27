class Config:
    SECRET_KEY = 'super-secret-key-para-jwt'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:12345@localhost/bar_inventory_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CATALOG_SERVICE_URL = 'http://127.0.0.1:5002/api'