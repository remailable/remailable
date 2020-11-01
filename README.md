<h1 align="center">ReMailable</h1>
<p align="center">email documents to your <a href="https://remarkable.com">ReMarkable</a> tablet</p>

![GitHub repo size](https://img.shields.io/github/repo-size/j6k4m8/remailable?style=for-the-badge) ![GitHub last commit](https://img.shields.io/github/last-commit/j6k4m8/remailable?style=for-the-badge)
![This repo is pretty dope.](https://img.shields.io/badge/pretty%20dope-%F0%9F%91%8C-blue?style=for-the-badge) ![This repo is licensed under Apache 2.0](https://img.shields.io/github/license/j6k4m8/remailable?style=for-the-badge)

You can use this by emailing a PDF to `remailable@[your-custom-domain]`. Read on for instructions.

## Using the public instance of _remailable_ for free

I host a version of this that you can use for free. Emails are not kept and do not go to a real mailbox. (Email binaries are deleted after 24 hours automatically.)

### Setup

Write a new email to [remailable@getneutrality.org](mailto:remailable@getneutrality.org) with nothing in the body and your [new-device ReMarkable code](https://my.remarkable.com/connect/mobile) in the subject line.

### Usage

Email [remailable@getneutrality.org](mailto:remailable@getneutrality.org) with a PDF attachment. It will be delivered to your ReMarkable tablet.

### Limitations

-   Under 30MB please!
-   That's it :)

## Making Your Own

## To Set Up Before You Start

-   [ ] You'll need to set up an SES domain ([AWS Docs](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-getting-started-before.html)).
-   [ ] Verify the domain ([AWS Docs](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-getting-started-verify.html)).
-   [ ] Set up a S3 hook upon email receipt so that emails are routed to an S3 bucket. (See docs above)
-   [ ] Create a `config.py` file in this directory with the following contents:

```python
class Config:
    BUCKET_NAME = "[YOUR BUCKET NAME]"
    BUCKET_PREFIX = "attachments" # optional; based upon your S3 rule above
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
