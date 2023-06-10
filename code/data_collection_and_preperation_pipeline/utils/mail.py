from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import boto3
from botocore.exceptions import ClientError
from utils.base import Base


class Mail(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def send(self, body, subject='Subject', replyto=""):
        """
        recipient, cc_email, and bcc_email are all an email or a list of emails to send to.
        """
        recipient = self.config.mail.email_to

        cc_email = None
        bcc_email = None

        if len(recipient) == 0:
            raise Exception("No email addresses to send to.")

        client = boto3.client('ses', region_name           = self.config.mail.AWS_region,
                                     aws_access_key_id     = self.config.mail.AWS_key_id,
                                     aws_secret_access_key = self.config.mail.AWS_key
                              )

        if not cc_email: cc_email = []
        if not bcc_email: bcc_email = []

        if type(recipient) != list: recipient = [recipient]
        if type(cc_email) != list: cc_email = [cc_email]
        if type(bcc_email) != list: bcc_email = [bcc_email]

        recipient     = ','.join(recipient).replace('"',"'")     # Mail Recipient
        cc_email      = ','.join(cc_email).replace('"',"'")      # Mail Recipient
        bcc_email     = ','.join(bcc_email).replace('"',"'")     # Mail Recipient
        replyto       = ','.join(replyto).replace('"',"'")       # Mail Recipient
        subject       = subject.replace('"',"'")                 # The subject line for the email.
        body_text     = (body.replace('"',"'"))             # The email body for recipients with non-HTML email clients.
        from_address  = self.config.mail.email_from.replace('"',"'")    # The sender email

        # ------------------------------------------------------------------
        # CREATE THE MESSAGE FROM THE DATABASE FIELDS
        # ------------------------------------------------------------------
        msg_string   = self.create_MIME_message(subject,from_address,recipient,cc_email,bcc_email,body_text,replyto)
        message_dict = {'Data': msg_string}

        # ------------------------------------------------------------------
        # TRY TO SEND THE MESSAGE
        # ------------------------------------------------------------------
        self.debug(f"Sending email to \"{recipient}\"")
        try:
            client.send_raw_email(RawMessage=message_dict)
        except Exception as e:
            self.err(f"Error sending mail. {self.exc(e)}")

    def create_MIME_message(self, subject,from_address,recipient, cc_email, bcc_email, body_text, replyto):
        """
        CREATES A MIME TYPE MESSAGE.
        using the email library, this function creates an email in plain text,
        """

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



