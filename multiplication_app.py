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

        # This is where the game begins. This section of is code only executed if the login form works,
        # and if the user is successfully logged in.
        if user:
            correct = 0
            wrong = 0

            cookies = http.cookies.SimpleCookie()
            if 'HTTP_COOKIE' in environ:
                cookies.load(environ['HTTP_COOKIE'])
                if 'correct' in cookies:
                    correct = int(cookies['correct'].value)
                if 'wrong' in cookies:
                    wrong = int(cookies['wrong'].value)
                # [INSERT CODE FOR COOKIES HERE]

            page = '<!DOCTYPE html><html><head><title>Multiply with Score</title></head><body>'
            if 'factor1' in params and 'factor2' in params and 'answer' in params:
                if (int(params['factor1'][0]) * int(params['factor2'][0])) == int(params['answer'][0]):
                    page += '<head><h1 style="background-color: lightgreen">Correct, {} x {} = {}</h1></head>'.format(params['factor1'][0], params['factor2'][0], params['answer'][0])
                    page += '<a href="/account">Back to multiplication game! --> </a>'
                    correct += 1
                    headers += [('Set-Cookie', 'correct={}'.format(correct))]

                else:
                    page += '<head><h1 style="background-color: red">Incorrect, {} x {} = {}</h1></head>'.format(params['factor1'][0], params['factor2'][0], int(params['factor1'][0]) * int(params['factor2'][0]))
                    page += '<a href="/account">Back to multiplication game! --> </a>'
                    wrong += 1
                    headers += [('Set-Cookie', 'wrong={}'.format(wrong))]

                return [page.encode()]

            elif 'reset' in params:
                correct = 0
                wrong = 0

            headers.append(('Set-Cookie', 'correct={}'.format(correct)))
            headers.append(('Set-Cookie', 'wrong={}'.format(wrong)))

            f1 = random.randrange(10) + 1
            f2 = random.randrange(10) + 1

            page = page + '<h1>What is {} x {}?</h1>'.format(f1, f2)

            answer = [f1*f2, random.randrange(f2+10, 100), (f1*f2) + 5, random.randrange(70, 100)]
            random.shuffle(answer)

            hyperlink = '<a href="/account?username={}&amp;password={}&amp;factor1={}&amp;factor2={}&amp;answer={}">{}</a><br>'

            ans_1 = hyperlink.format(un, pw, f1, f2, answer[0], answer[0])
            ans_2 = hyperlink.format(un, pw, f1, f2, answer[1], answer[1])
            ans_3 = hyperlink.format(un, pw, f1, f2, answer[2], answer[2])
            ans_4 = hyperlink.format(un, pw, f1, f2, answer[3], answer[3])

            page += '''
            A: {}<br>
            B: {}<br>
            C: {}<br>
            D: {}<br>
            <br>
            '''.format(ans_1, ans_2, ans_3, ans_4)


            page += '''<h2>Score</h2>
            Correct: {}<br>
            Wrong: {}<br>
            <a href="/account?reset=true">Reset</a>
            </body></html>'''.format(correct, wrong)

            return [page.encode()]
        else:
            return ['Not logged in. <a href="/">Login</a>'.encode()]

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
