import wsgiref.simple_server
import urllib.parse
import sqlite3
import http.cookies
import random

connection = sqlite3.connect('users.db')
stmt = "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
cursor = connection.cursor()
result = cursor.execute(stmt)
r = result.fetchall()
if (r == []):
    exp = 'CREATE TABLE users (username,password)'
    connection.execute(exp)

def application(environ, start_response):
    headers = [('Content-Type', 'text/html; charset=utf-8')]

    path = environ['PATH_INFO']
    params = urllib.parse.parse_qs(environ['QUERY_STRING'])
    un = params['username'][0] if 'username' in params else None
    pw = params['password'][0] if 'password' in params else None

    if path == '/register' and un and pw:
        user = cursor.execute('SELECT * FROM users WHERE username = ?', [un]).fetchall()
        if user:
            start_response('200 OK', headers)
            return ['Sorry, username {} is taken'.format(un).encode()]
        else:
            connection.execute('INSERT INTO users VALUES (?, ?)', [un, pw])
            connection.commit()
            start_response('200 OK', headers)
            return ['Username {} been successfully registered. Go to <a href="/">Login</a>'.format(un).encode()]

    elif path == '/login' and un and pw:
        user = cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', [un, pw]).fetchall()
        if user:
            headers.append(('Set-Cookie', 'session={}:{}'.format(un, pw)))
            start_response('200 OK', headers)
            return ['User {} successfully logged in. <br> Go to your <a href="/account">Account</a>!'.format(un).encode()]
        else:
            start_response('200 OK', headers)
            return ['Incorrect username or password. <a href="/">Register</a>'.encode()]

    elif path == '/logout':
        headers.append(('Set-Cookie', 'session=0; expires=Thu, 01 Jan 1970 00:00:00 GMT'))
        start_response('200 OK', headers)
        return ['Logged out. <a href="/">Login</a>'.encode()]

    elif path == '/account':
        start_response('200 OK', headers)

        if 'HTTP_COOKIE' not in environ:
            return ['Not logged in <a href="/">Login</a>'.encode()]

        cookies = http.cookies.SimpleCookie()
        cookies.load(environ['HTTP_COOKIE'])
        if 'session' not in cookies:
            return ['Not logged in <a href="/">Login</a>'.encode()]

        [un, pw] = cookies['session'].value.split(':')
        user = cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', [un, pw]).fetchall()

    elif path == '/':
        start_response('200 OK', headers)
        page = '''
        <!DOCTYPE html>
        <html>
        <form action="/register" style="background-color:lightblue">
            <h1>Register</h1>
            New? Create your account now! <br>
            <br>Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Register">
        </form> <br>
        <form action="/login" style="background-color:gold">
            <h1>Login</h1>
            Welcome back!  <br>
            <br>Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Log in">
        </form>
        </html>'''

        return [page.encode()]

    else:
        start_response('404 Not Found', headers)
        return ['Status 404: Resource not found'.encode()]


httpd = wsgiref.simple_server.make_server('', 8000, application)
httpd.serve_forever()
