<h1 align="center"><a href="https://remailable.getneutrality.org/">ReMailable</a></h1>
<p align="center">email documents to your <a href="https://remarkable.com">ReMarkable</a> tablet</p>

![GitHub repo size](https://img.shields.io/github/repo-size/j6k4m8/remailable?style=for-the-badge) ![GitHub last commit](https://img.shields.io/github/last-commit/j6k4m8/remailable?style=for-the-badge)
![This repo is pretty dope.](https://img.shields.io/badge/pretty%20dope-%F0%9F%91%8C-blue?style=for-the-badge) ![This repo is licensed under Apache 2.0](https://img.shields.io/github/license/j6k4m8/remailable?style=for-the-badge)

You can use this by emailing a PDF to `remailable@[your-custom-domain]`. Read on for instructions.

## Using <a href="https://remailable.getneutrality.org/">the public instance of _remailable_</a> for free

I host a version of this that you can use for free. Emails are not kept and do not go to a real mailbox. (Email binaries are deleted after 24 hours automatically.)

### Setup

Write a new email to [remailable@getneutrality.org](mailto:remailable@getneutrality.org) with nothing in the body and your [new-device ReMarkable code](https://my.remarkable.com/connect/mobile) in the subject line.

### Usage

Email [remailable@getneutrality.org](mailto:remailable@getneutrality.org) with a PDF attachment. It will be delivered to your ReMarkable tablet.

### Limitations

-   Under 30MB please!
-   That's it :)

### Issues?

If you encounter issues, please feel free to reach out. @j6m8 on reddit, submit an issue here, or shoot me an email.

To delete your account, send a message with the subject line "Unsubscribe". Your account will be deleted and you will not receive any more emails from Remailable.

## Making Your Own

I'm trying to migrate as much of this as possible to automation/scripts. Unfortunately, much of this must be done through the AWS UI console, and because there's a human in the loop, it can take a few days!

## To Set Up Before You Start

-   [ ] You'll need to set up an SES domain ([AWS Docs](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-getting-started-before.html)).
-   [ ] Verify the domain ([AWS Docs](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-getting-started-verify.html)).
-   [ ] If you're planning on distributing to public users (i.e. don't know your recipients' emails a priori), you must also [move your SES account into production mode](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/request-production-access.html). Note that this is not necessary if you are just setting up a personal deploy: In that case, you can just add your personal email address to the list of approved sandbox recipients. Note that this process has an AWS human in the loop, and will take a while.
-   [ ] Verify your sender email address (same as you use for `Config.EMAIL_SENDER` in config.py). You can do this automatically with `python3 provision.py verify-sender`.
-   [ ] Set up a S3 hook upon email receipt so that emails are routed to an S3 bucket. (See docs above)
-   [ ] Add the `SESSendEmail` (or just `AmazonSESFullAccess`) policies to your Zappa-created role. (This role will be called something like `remailable-blah-ZappaLambdaExecutionRole`)
-   [ ] Create a `config.py` file in this directory with the following contents:

```python
class Config:
    AWS_REGION = "us-east-1"

    BUCKET_NAME = "[YOUR BUCKET NAME]"
    BUCKET_PREFIX = "attachments" # optional; based upon your S3 rule above

    # The email-sender that you verified above. Leave as empty string
    # if Config.SEND_EMAILS is False.
    EMAIL_SENDER = "Remailable <YOUR_USER@DOMAIN.com>"

    # Set to False if you won't be sending receipt emails:
    SEND_EMAILS = True
```

## To Set Up While You Start

```shell
zappa init
```

You'll need to configure your Zappa file to look like the following:

```js
{
    "production": {
        "app_function": "lambda_main.APP",
        "aws_region": "us-east-1",
        "project_name": "remailable", // call this something cute :)
        "runtime": "python3.7",
        "s3_bucket": [NEW BUCKET NAME] // different bucket name than above
        "events": [
            {
                "function": "lambda_main.upload_handler",
                "event_source": {
                    "arn": "arn:aws:s3:::[Config.BUCKET_NAME GOES HERE]",
                    "events": ["s3:ObjectCreated:*"]
                }
            }
        ]
    }
}
```

## Why?

I love emailing documents to my Kindle. It's a very natural way of sharing a PDF for many people, and in my opinion it's a huge shortcoming of the ReMarkable ecosystem. So now it's fixed :)

## You May Also Like...

-   [Goosepaper](https://github.com/j6k4m8/goosepaper): A daily, customizable, morning news brief delivered to your ReMarkable
