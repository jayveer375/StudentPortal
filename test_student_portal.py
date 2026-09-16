import urllib.request, http.cookiejar, json
import psycopg2, os
from dotenv import load_dotenv

def test_full_student_flow():
    base_url = 'http://127.0.0.1:5000'
    print("[START] Starting Student Portal Verification Suite...")
    
    # 1. Test Admin Login
    cj_admin = http.cookiejar.CookieJar()
    opener_admin = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj_admin))
    req = urllib.request.Request(
        f'{base_url}/login',
        data=json.dumps({'username': 'Admin@gmail.com', 'password': 'admin@123'}).encode(),
        headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
    )
    res = opener_admin.open(req)
    admin_login_res = json.loads(res.read().decode())
    print('1. Admin login response:', admin_login_res)
    assert admin_login_res['success'] == True
    assert admin_login_res['redirect'] == '/'
    
    # 2. Test Student Initial Login (email + enrollment number)
    cj_student = http.cookiejar.CookieJar()
    opener_student = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj_student))
    req = urllib.request.Request(
        f'{base_url}/login',
        data=json.dumps({'username': 'jayveervora47@gmail.com', 'password': '246171063001'}).encode(),
        headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
    )
    res = opener_student.open(req)
    student_login_res = json.loads(res.read().decode())
    print('2. Student initial login response:', student_login_res)
    assert student_login_res['success'] == True
    assert student_login_res['redirect'] == '/student'
    
    # 3. Test Student Portal Page Loading & Seat Allotment View
    req = urllib.request.Request(f'{base_url}/student')
    res = opener_student.open(req)
    html = res.read().decode()
    print('3. Student portal HTTP status:', res.status)
    assert 'Allocated Classroom' in html or 'Classroom' in html
    assert '1A110' in html
    assert '246171063001' in html
    assert 'Jayveer vora' in html
    print('   [OK] Classroom, Block 1A110, Enrollment 246171063001 confirmed in HTML!')
    
    # 4. Test Student Name Update
    req = urllib.request.Request(
        f'{base_url}/student/update-name',
        data=json.dumps({'name': 'Jayveer Vora (Verified)'}).encode(),
        headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
    )
    res = opener_student.open(req)
    name_res = json.loads(res.read().decode())
    print('4. Name update response:', name_res)
    assert name_res['success'] == True
    
    # Verify name updated in portal
    html_after_name = opener_student.open(urllib.request.Request(f'{base_url}/student')).read().decode()
    assert 'Jayveer Vora (Verified)' in html_after_name
    print('   [OK] Name verified updated in HTML view!')
    
    # 5. Test Change Password with incorrect current password
    try:
        req = urllib.request.Request(
            f'{base_url}/student/change-password',
            data=json.dumps({'current_password': 'wrongpassword', 'new_password': 'NewPassword123', 'confirm_password': 'NewPassword123'}).encode(),
            headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
        )
        opener_student.open(req)
        assert False, 'Should have failed with wrong current password'
    except urllib.error.HTTPError as err:
        err_json = json.loads(err.read().decode())
        print('5a. Wrong current password rejected (expected):', err_json)
        assert err_json['success'] == False
    
    # 6. Test Change Password with valid current password (initial enrollment number)
    req = urllib.request.Request(
        f'{base_url}/student/change-password',
        data=json.dumps({'current_password': '246171063001', 'new_password': 'NewPassword123', 'confirm_password': 'NewPassword123'}).encode(),
        headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
    )
    res = opener_student.open(req)
    pwd_res = json.loads(res.read().decode())
    print('5b. Password change response:', pwd_res)
    assert pwd_res['success'] == True
    
    # 7. Test Login with old password (should fail)
    try:
        cj_fail = http.cookiejar.CookieJar()
        opener_fail = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj_fail))
        req = urllib.request.Request(
            f'{base_url}/login',
            data=json.dumps({'username': 'jayveervora47@gmail.com', 'password': '246171063001'}).encode(),
            headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
        )
        opener_fail.open(req)
        assert False, 'Old password should have been rejected'
    except urllib.error.HTTPError as err:
        print('6. Old password rejected as expected (HTTP 401)')
        
    # 8. Test Login with new password (should succeed)
    cj_new = http.cookiejar.CookieJar()
    opener_new = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj_new))
    req = urllib.request.Request(
        f'{base_url}/login',
        data=json.dumps({'username': 'jayveervora47@gmail.com', 'password': 'NewPassword123'}).encode(),
        headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
    )
    res = opener_new.open(req)
    new_login_res = json.loads(res.read().decode())
    print('7. Login with new password:', new_login_res)
    assert new_login_res['success'] == True
    assert new_login_res['redirect'] == '/student'
    
    # 9. Clean up test data (reset name to 'Jayveer vora' and password to NULL for clean state)
    load_dotenv()
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute("UPDATE students SET name = 'Jayveer vora', password = NULL WHERE enrollment_number = 246171063001")
    cur.execute("UPDATE seating_allocations SET student_name = 'Jayveer vora' WHERE enrollment_number = 246171063001")
    conn.commit()
    conn.close()
    print('8. Cleaned up student record back to original pristine state.')
    print('\n[SUCCESS] ALL 8 AUTOMATED TESTS PASSED WITH 100% SUCCESS!')

if __name__ == '__main__':
    test_full_student_flow()
