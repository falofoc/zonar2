@app.route("/test_email")
@login_required
def test_email():
    try:
        from flask_mail import Message
        from app import mail
        import os
        sender_email = os.environ.get("MAIL_DEFAULT_SENDER", "zoonarcom@gmail.com")
        body_text = f'''Hello {current_user.username},

This is a test email from your ZONAR account.

If you received this email, it means your email configuration is working correctly.

Best regards,
ZONAR Team'''
        msg = Message(
            subject="Test Email from ZONAR",
            sender=sender_email,
            recipients=[current_user.email],
            body=body_text
        )
        mail.send(msg)
        flash("Test email sent successfully! Please check your inbox.", "success")
    except Exception as e:
        flash(f"Error sending email: {str(e)}", "danger")
        print(f"Email error: {e}")
    return redirect(url_for("settings"))
