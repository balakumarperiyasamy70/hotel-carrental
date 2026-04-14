import os
import random
import string
from datetime import datetime, date
from functools import wraps
from io import BytesIO

import pymysql
from dotenv import load_dotenv
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, send_file, abort)
from werkzeug.security import generate_password_hash, check_password_hash

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

load_dotenv()
app = Flask(__name__)

import urllib.request, urllib.parse
RECAPTCHA_SECRET = '6LezIZwsAAAAAC4wfNWUsFejww_H9yITQuPkmazz'

def verify_recaptcha(token):
    try:
        data = urllib.parse.urlencode({'secret': RECAPTCHA_SECRET, 'response': token}).encode()
        req = urllib.request.urlopen('https://www.google.com/recaptcha/api/siteverify', data, timeout=5)
        result = __import__('json').loads(req.read().decode())
        return result.get('success', False)
    except Exception:
        return False
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# ── DB ──────────────────────────────────────────────────────────────────────

def get_db():
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'carrental'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'sandscarrental'),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def query(sql, args=(), one=False, commit=False):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            if commit:
                conn.commit()
                return cur.lastrowid
            result = cur.fetchone() if one else cur.fetchall()
            return result
    finally:
        conn.close()

# ── HELPERS ──────────────────────────────────────────────────────────────────

def gen_ref():
    return '#SND-' + ''.join(random.choices(string.digits, k=4))

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── PUBLIC ROUTES ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    fleet = query("SELECT * FROM fleet WHERE status = 'available' ORDER BY daily_rate")
    return render_template('index.html', fleet=fleet)

@app.route('/book', methods=['POST'])
def book():
    data = request.form
    recaptcha_token = data.get('g-recaptcha-response', '')
    if not verify_recaptcha(recaptcha_token):
        flash('reCAPTCHA verification failed. Please try again.', 'error')
        return redirect(url_for('index'))
    fleet_id  = data.get('fleet_id')
    pickup    = data.get('pickup_date')
    ret       = data.get('return_date')

    # Calculate days
    try:
        d1   = datetime.strptime(pickup, '%Y-%m-%d').date()
        d2   = datetime.strptime(ret,    '%Y-%m-%d').date()
        days = max(1, (d2 - d1).days)
    except Exception:
        flash('Invalid dates selected.', 'error')
        return redirect(url_for('index'))

    car = query("SELECT * FROM fleet WHERE id = %s", (fleet_id,), one=True)
    if not car:
        flash('Vehicle not found.', 'error')
        return redirect(url_for('index'))

    rate        = float(car['daily_rate'])
    loc_fee     = 15.00
    total       = round(rate * days + loc_fee, 2)
    ref         = gen_ref()

    query("""
        INSERT INTO bookings
          (ref, fleet_id, first_name, last_name, email, phone, address,
           license_no, license_state, pickup_location, dropoff_location,
           pickup_date, return_date, days, daily_rate, location_fee, total, notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        ref, fleet_id,
        data.get('first_name'), data.get('last_name'),
        data.get('email'),      data.get('phone'),
        data.get('address'),    data.get('license_no'),
        data.get('license_state', 'Arkansas'),
        data.get('pickup_location'), data.get('dropoff_location'),
        pickup, ret, days, rate, loc_fee, total,
        data.get('notes', '')
    ), commit=True)

    return render_template('confirmation.html', ref=ref, car=car,
                           days=days, total=total,
                           pickup=pickup, ret=ret,
                           first_name=data.get('first_name'))

@app.route('/status/<ref>')
def booking_status(ref):
    booking = query("SELECT b.*, f.name as car_name FROM bookings b LEFT JOIN fleet f ON b.fleet_id=f.id WHERE b.ref=%s", (ref,), one=True)
    if not booking:
        abort(404)
    return render_template('status.html', booking=booking)

# ── ADMIN ROUTES ──────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = query("SELECT * FROM admin_users WHERE username=%s", (username,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['admin_logged_in'] = True
            session['admin_name']      = user['name']
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    bookings = query("""
        SELECT b.*, f.name as car_name, f.category
        FROM bookings b LEFT JOIN fleet f ON b.fleet_id=f.id
        ORDER BY b.created_at DESC
    """)
    fleet    = query("SELECT * FROM fleet ORDER BY category")
    stats    = {
        'pending':   query("SELECT COUNT(*) as c FROM bookings WHERE status='pending'",   one=True)['c'],
        'active':    query("SELECT COUNT(*) as c FROM bookings WHERE status='active'",    one=True)['c'],
        'total':     query("SELECT COUNT(*) as c FROM bookings",                          one=True)['c'],
        'revenue':   query("SELECT COALESCE(SUM(total),0) as s FROM bookings WHERE status IN ('approved','active','completed')", one=True)['s'],
    }
    return render_template('admin.html', bookings=bookings, fleet=fleet, stats=stats)

@app.route('/admin/booking/<int:bid>/approve', methods=['POST'])
@login_required
def approve_booking(bid):
    note = request.form.get('admin_note', '')
    query("""UPDATE bookings SET status='approved', admin_note=%s,
             reviewed_by=%s, reviewed_at=NOW() WHERE id=%s""",
          (note, session.get('admin_name', 'Admin'), bid), commit=True)
    flash('Booking approved successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/booking/<int:bid>/decline', methods=['POST'])
@login_required
def decline_booking(bid):
    note = request.form.get('admin_note', '')
    query("""UPDATE bookings SET status='declined', admin_note=%s,
             reviewed_by=%s, reviewed_at=NOW() WHERE id=%s""",
          (note, session.get('admin_name', 'Admin'), bid), commit=True)
    flash('Booking declined.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/booking/<int:bid>/activate', methods=['POST'])
@login_required
def activate_booking(bid):
    query("UPDATE bookings SET status='active' WHERE id=%s", (bid,), commit=True)
    query("UPDATE fleet SET status='rented' WHERE id=(SELECT fleet_id FROM bookings WHERE id=%s)", (bid,), commit=True)
    flash('Booking marked as active.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/booking/<int:bid>/complete', methods=['POST'])
@login_required
def complete_booking(bid):
    query("UPDATE bookings SET status='completed' WHERE id=%s", (bid,), commit=True)
    query("UPDATE fleet SET status='available' WHERE id=(SELECT fleet_id FROM bookings WHERE id=%s)", (bid,), commit=True)
    flash('Booking completed.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/fleet/<int:fid>/status', methods=['POST'])
@login_required
def update_fleet_status(fid):
    status = request.form.get('status')
    query("UPDATE fleet SET status=%s WHERE id=%s", (status, fid), commit=True)
    flash('Fleet status updated.', 'success')
    return redirect(url_for('admin_dashboard'))

# ── PDF AGREEMENT ─────────────────────────────────────────────────────────────

@app.route('/admin/booking/<int:bid>/agreement')
@login_required
def generate_agreement(bid):
    b = query("""SELECT bk.*, f.name as car_name, f.category, f.year,
                        f.plate, f.color, f.vin, f.transmission, f.seats
                 FROM bookings bk LEFT JOIN fleet f ON bk.fleet_id=f.id
                 WHERE bk.id=%s""", (bid,), one=True)
    if not b:
        abort(404)

    BLUE_DARK  = colors.HexColor('#042C53')
    BLUE_MID   = colors.HexColor('#185FA5')
    BLUE_LIGHT = colors.HexColor('#E6F1FB')
    GRAY_LIGHT = colors.HexColor('#F1EFE8')
    GRAY_MID   = colors.HexColor('#B4B2A9')
    BLACK      = colors.HexColor('#1a1a1a')

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch,  bottomMargin=0.75*inch)

    S   = lambda name, **kw: ParagraphStyle(name, **kw)
    st_h1   = S('h1',  fontSize=22, textColor=BLUE_DARK,  leading=28, spaceAfter=2,  fontName='Helvetica-Bold')
    st_sub  = S('sub', fontSize=10, textColor=BLUE_MID,   leading=14, fontName='Helvetica')
    st_sec  = S('sec', fontSize=9,  textColor=BLUE_MID,   leading=12, spaceBefore=14, spaceAfter=4, fontName='Helvetica-Bold')
    st_body = S('b',   fontSize=9.5,textColor=BLACK,      leading=14, fontName='Helvetica')
    st_sm   = S('sm',  fontSize=8,  textColor=colors.HexColor('#5F5E5A'), leading=12, fontName='Helvetica')
    st_bold = S('bd',  fontSize=9.5,textColor=BLACK,      leading=14, fontName='Helvetica-Bold')

    def kv_table(rows):
        data = [[Paragraph('<b>'+k+'</b>', st_sm), Paragraph(v or '—', st_body)] for k,v in rows]
        t = Table(data, colWidths=[2.2*inch, 4.8*inch])
        t.setStyle(TableStyle([
            ('VALIGN',       (0,0),(-1,-1),'TOP'),
            ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white, GRAY_LIGHT]),
            ('TOPPADDING',   (0,0),(-1,-1),5),
            ('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LEFTPADDING',  (0,0),(-1,-1),8),
            ('RIGHTPADDING', (0,0),(-1,-1),8),
            ('LINEBELOW',    (0,0),(-1,-2),0.25,GRAY_MID),
        ]))
        return t

    story = []

    # Header
    hdr = Table([[
        Paragraph('Sands Car Rental', S('ch',fontSize=14,textColor=BLUE_DARK,fontName='Helvetica-Bold')),
        Paragraph('357 S Division St, Blytheville AR 72315<br/>(870) 763-4588  |  rental@sandshotel.us',
                  S('ca',fontSize=8,textColor=colors.HexColor('#5F5E5A'),leading=12,alignment=TA_RIGHT,fontName='Helvetica'))
    ]], colWidths=[3.5*inch, 3.5*inch])
    hdr.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),BLUE_LIGHT),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),
        ('LEFTPADDING',(0,0),(0,-1),14),('RIGHTPADDING',(-1,0),(-1,-1),14),
    ]))
    story += [hdr, Spacer(1,14)]

    story.append(Paragraph('Car Rental Agreement', st_h1))
    story.append(Paragraph('Reference: <b>'+str(b['ref'])+'</b>  &nbsp;&nbsp;  Issued: '+datetime.now().strftime('%B %d, %Y'), st_sub))
    story.append(Spacer(1,8))
    story.append(HRFlowable(width='100%', thickness=1.5, color=BLUE_MID, spaceAfter=6, spaceBefore=6))

    story.append(Paragraph('1. CUSTOMER INFORMATION', st_sec))
    story.append(kv_table([
        ('Full name',        (b['first_name'] or '') + ' ' + (b['last_name'] or '')),
        ('Email',            b['email']),
        ('Phone',            b['phone']),
        ('Address',          b['address'] or '—'),
        ("Driver's license", str(b['license_no']) + '  (State: ' + str(b['license_state']) + ')'),
    ]))
    story.append(Spacer(1,6))

    story.append(Paragraph('2. VEHICLE INFORMATION', st_sec))
    story.append(kv_table([
        ('Vehicle',   str(b['year'] or '') + ' ' + str(b['car_name'] or '')),
        ('Category',  b['category'] or '—'),
        ('Color',     b['color']    or '—'),
        ('Plate',     b['plate']    or '—'),
        ('VIN',       b['vin']      or '—'),
    ]))
    story.append(Spacer(1,6))

    story.append(Paragraph('3. RENTAL PERIOD', st_sec))
    story.append(kv_table([
        ('Pick-up date',    str(b['pickup_date'])),
        ('Pick-up location',b['pickup_location']  or '—'),
        ('Return date',     str(b['return_date'])),
        ('Return location', b['dropoff_location'] or '—'),
        ('Total days',      str(b['days']) + ' day(s)'),
    ]))
    story.append(Spacer(1,6))

    story.append(Paragraph('4. CHARGES & PAYMENT', st_sec))
    sub   = float(b['daily_rate']) * int(b['days'])
    total = float(b['total'])
    cdata = [
        [Paragraph('<b>Description</b>',st_sm), Paragraph('<b>Amount</b>',st_sm)],
        [Paragraph('Daily rate ($'+str(b['daily_rate'])+') x '+str(b['days'])+' days',st_body), Paragraph('$'+'{:.2f}'.format(sub),st_body)],
        [Paragraph('Location fee',st_body),   Paragraph('$'+'{:.2f}'.format(float(b['location_fee'])),st_body)],
        [Paragraph('Insurance',st_body),       Paragraph('$0.00',st_body)],
        [Paragraph('<b>Total due</b>',st_bold),Paragraph('<b>$'+'{:.2f}'.format(total)+'</b>',st_bold)],
        [Paragraph('Security deposit (refundable)',st_sm), Paragraph('$200.00',st_sm)],
    ]
    ct = Table(cdata, colWidths=[5.0*inch, 2.0*inch])
    ct.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),BLUE_DARK),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0),8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,GRAY_LIGHT]),
        ('LINEABOVE',(0,4),(-1,4),1,BLUE_MID),
        ('BACKGROUND',(0,4),(-1,4),BLUE_LIGHT),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('ALIGN',(1,0),(1,-1),'RIGHT'),
    ]))
    story.append(ct)
    story.append(Spacer(1,6))

    story.append(Paragraph('5. TERMS & CONDITIONS', st_sec))
    terms = [
        '5.1  Vehicle must be returned in same condition with a full tank of fuel.',
        '5.2  Renter is responsible for all traffic fines, tolls, and parking violations.',
        '5.3  Smoking is strictly prohibited. A $250 cleaning fee will apply.',
        '5.4  Pets are not permitted without prior written consent.',
        '5.5  Vehicle may not be driven outside agreed state(s) without written approval.',
        '5.6  Any damage, accident, or theft must be reported immediately.',
        '5.7  Security deposit refunded within 5 business days after vehicle inspection.',
        '5.8  Late returns charged at daily rate, pro-rated per hour after 1-hour grace period.',
        '5.9  This agreement is governed by the laws of the State of Arkansas.',
    ]
    for t in terms:
        story.append(Paragraph(t, st_sm))
        story.append(Spacer(1,3))

    story.append(Spacer(1,12))
    story.append(Paragraph('6. SIGNATURES', st_sec))
    story.append(Paragraph('By signing below, both parties agree to the terms stated in this agreement.', st_sm))
    story.append(Spacer(1,16))

    sig = Table([
        [Paragraph('<b>Customer signature</b>',st_sm), '', Paragraph('<b>Authorized by (Sands Car Rental)</b>',st_sm), ''],
        [Paragraph('____________________________',st_body), '', Paragraph('____________________________',st_body), ''],
        [Paragraph((b['first_name'] or '') + ' ' + (b['last_name'] or ''),st_sm), '', Paragraph(str(b['reviewed_by'] or 'Admin'),st_sm), ''],
        [Paragraph('Date: ___________________',st_sm), '', Paragraph('Date: ___________________',st_sm), ''],
    ], colWidths=[2.8*inch, 0.5*inch, 2.8*inch, 0.9*inch])
    sig.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'BOTTOM'),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(sig)

    story.append(Spacer(1,20))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRAY_MID, spaceAfter=6))
    story.append(Paragraph(
        'Sands Car Rental  |  357 S Division St, Blytheville AR 72315  |  (870) 763-4588  |  carrental.sandshotel.us',
        S('ft',fontSize=7.5,textColor=GRAY_MID,alignment=TA_CENTER,fontName='Helvetica')
    ))

    doc.build(story)
    buf.seek(0)
    filename = 'rental-agreement-' + str(b['ref']).replace('#','') + '.pdf'
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)

# ── ADMIN FLEET ───────────────────────────────────────────────────────────────

@app.route('/admin/fleet/add', methods=['POST'])
@login_required
def add_fleet():
    d = request.form
    query("""INSERT INTO fleet (name,category,year,transmission,seats,daily_rate,plate,color,features,icon)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
          (d['name'],d['category'],d['year'],d['transmission'],d['seats'],
           d['daily_rate'],d['plate'],d['color'],d['features'],d['icon']), commit=True)
    flash('Vehicle added to fleet.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=False, port=8005)
