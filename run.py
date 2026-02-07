from app import create_app

app = create_app()

if __name__ == '__main__':
    # host='0.0.0.0' is REQUIRED for external access (like your mobile)
    app.run(host='0.0.0.0', port=3000, debug=True)