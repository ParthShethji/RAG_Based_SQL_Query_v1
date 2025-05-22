class DBConfig:
    def __init__(self):
        # Update these values with your actual MySQL credentials
        self.host = "localhost"
        self.user = ""  # Change this to your MySQL username
        self.password = ""  # Change this to your MySQL password
        self.database = ""  # Change this to your database name
        self.port = 3306
        self.charset = "utf8mb4"

    def get_connection_params(self):
        return {
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "port": self.port,
            "charset": self.charset
        }
