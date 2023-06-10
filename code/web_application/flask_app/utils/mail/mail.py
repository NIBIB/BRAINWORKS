from flask import current_app as app
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import boto3
from botocore.exceptions import ClientError

AWS_REGION    = ""  # e.g. "us-east-1"
ACCESS_KEY    = ""  # AWS access key ID
SECRET_KEY    = ""  # AWS access key

#Workmail account
EMAIL         = ""  # email to send from


#########################################################################################################

def send_mail(subject='Subject',
              recipient=[],
              cc_email=[],
              bcc_email=[],
              body_text="Hello",
              replyto=""
              ):
    if not app.config['EMAIL']:  # email disabled
        return Exception("Emailing has been disabled")
    if len(recipient) == 0:
        return Exception("No email addresses to send to.")
    if not EMAIL:
        return Exception("No email configured to send from")

    try:
        client = boto3.client('ses', region_name           = app.config['EMAIL_AWS_REGION'],
                                     aws_access_key_id     = app.config['EMAIL_ACCESS_KEY'],
                                     aws_secret_access_key = app.config['EMAIL_SECRET_KEY']
                              )

        # ------------------------------------------------------------------
        # PREPARE THE MESSAGE TO BE QUEUED
        # ------------------------------------------------------------------
        recipient     = ','.join(recipient).replace('"',"'")     # Mail Recipient
        cc_email      = ','.join(cc_email).replace('"',"'")      # Mail Recipient
        bcc_email     = ','.join(bcc_email).replace('"',"'")     # Mail Recipient
        replyto       = ','.join(replyto).replace('"',"'")       # Mail Recipient
        subject       = subject.replace('"',"'")                 # The subject line for the email.
        body_text     = (body_text.replace('"',"'"))             # The email body for recipients with non-HTML email clients.
        from_address  = app.config['EMAIL_ADDRESS'].replace('"',"'")  # The sender email

        # ------------------------------------------------------------------
        # CREATE THE MESSAGE FROM THE DATABASE FIELDS
        # ------------------------------------------------------------------
        msg_string   = create_MIME_message(subject,from_address,recipient,cc_email,bcc_email,body_text,replyto)
        message_dict = {'Data': msg_string }

        # ------------------------------------------------------------------
        # TRY TO SEND THE MESSAGE
        # ------------------------------------------------------------------
        response = client.send_raw_email(RawMessage=message_dict)
    except Exception as e:
        return e

    
#########################################################################################################
#    TITLE : CREATES A MIME TYPE MESSAGE
#          : using the email library, this function creates an email in plain text,
#########################################################################################################
def create_MIME_message(subject,from_address,recipient, cc_email, bcc_email,body_text,replyto):
    
    # Create the container (outer) email message.
    msg            =  MIMEMultipart('alternative')
    msg['Subject'] =  subject 
    msg['From']    =  from_address
    msg['To']      =  recipient
    msg['Cc']      =  cc_email
    msg['Bcc']     =  bcc_email

    msg.add_header('reply-to', replyto)

    # Generate the text/html content of the messages
    text = body_text 
    if text != '' and text is not None:
        part1 = MIMEText(text, 'plain')
        msg.attach(part1)
    
    msg_string = msg.as_string()
    return msg_string


# The following are string to be used as email content for various purposes.
# Use .format() to fill in the variables.
VERIFY_EMAIL_BODY = """
Hello {name},

Please click the link below to verify your BRAINWORKS account.
If you cannot click the link, please copy and paste it into your browser's address bar.
{verify_link}

This link is only valid for 24 hours.

If you did not sign up for this account, you may safely ignore this email.
"""

CHANGE_PASSWORD_BODY = """
Hello {name},

Someone requested a password reset for your BRAINWORKS account.

If this was you, please click the link below to securely change your password.
If you cannot click the link, please copy and paste it into your browser's address bar.
{reset_link}

This link is only valid for 24 hours.

If you did not request a password reset, you can safely ignore this email and your password will not change.
"""

LOCKED_ACCOUNT_BODY = """
Hello {name},

Someone tried to log into your account, and we have temporarily locked it until you re-verify your email.

Please click the link below to re-verify your BRAINWORKS account.
If you cannot click the link, please copy and paste it into your browser's address bar.
{verify_link}

This link is only valid for 24 hours
"""



