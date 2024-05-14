# config.py

class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'your_secret_key_here'
    DATABASE_URI = 'mysql://username:password@localhost/db_name'

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    # Add production-specific configurations here
    pass

# Choose the configuration based on the environment variable
# Example: export FLASK_ENV=development
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(env_name):
    return config_by_name.get(env_name, DevelopmentConfig)
