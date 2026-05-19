class Config:
    SECRET_KEY = 'super-secret-key-para-jwt' # Misma clave JWT de los otros servicios
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:12345@localhost/bar_inventory_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False