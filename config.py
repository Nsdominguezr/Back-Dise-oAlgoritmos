class Config:
    SECRET_KEY = 'super-secret-key-para-jwt' # ¡Debe ser la MISMA clave que usa Identity!
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:tu_password@localhost/bar_catalog_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False