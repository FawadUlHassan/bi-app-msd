# run.py
from my_bi_tool import create_app

app = create_app()

if __name__ == '__main__':
    # Debug mode for development
    app.run(debug=True, host='0.0.0.0', port=5000)

