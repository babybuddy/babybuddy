# Storage

## `ALLOW_UPLOADS`

*Default:* `True`

Whether to allow uploads (e.g., of Child photos). For some deployments (Heroku)
this setting will default to False due to the lack of available persistent storage.

## `AWS_ACCESS_KEY_ID`

*Default:* `None`

Required to access your AWS S3 bucket, should be uniquely generated per bucket
for security.

See also: [`AWS_STORAGE_BUCKET_NAME`](#aws_storage_bucket_name)

## `AWS_SECRET_ACCESS_KEY`

*Default:* `None`

Required to access your AWS S3 bucket, should be uniquely generated per bucket
for security.

See also: [`AWS_STORAGE_BUCKET_NAME`](#aws_storage_bucket_name)

## `AWS_STORAGE_BUCKET_NAME`

*Default:* `None`

If you would like to use AWS S3 for storage on ephemeral storage platforms like
Heroku you will need to create a bucket and add its name. See django-storages'
[Amazon S3 documentation](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html).

## `AWS_S3_ENDPOINT_URL`

*Default:* `None`

Custom URL to use when connecting to S3, including scheme.
This allows to use a S3-compatible storage service of another provider than AWS.
