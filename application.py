from app import create_app

# AWS looks for 'application', not 'app'
application = create_app()

if __name__ == "__main__":
    # This allows you to run it locally if you want, 
    # but AWS will import 'application' directly.
    application.run()