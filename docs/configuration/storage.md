# Storage

## `ALLOW_UPLOADS`

_Default:_ `True`

Whether to allow uploads (e.g., of Child photos).

## `AWS_ACCESS_KEY_ID`

_Default:_ `None`

Required to access your AWS S3 bucket, should be uniquely generated per bucket
for security.

See also: [`AWS_STORAGE_BUCKET_NAME`](#aws_storage_bucket_name)

## `AWS_SECRET_ACCESS_KEY`

_Default:_ `None`

Required to access your AWS S3 bucket, should be uniquely generated per bucket
for security.

See also: [`AWS_STORAGE_BUCKET_NAME`](#aws_storage_bucket_name)

## `AWS_STORAGE_BUCKET_NAME`

_Default:_ `None`

If you would like to use AWS S3 for storage you will need to create a bucket and add
its name. See django-storages' [Amazon S3 documentation](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html).

## `AWS_S3_ENDPOINT_URL`

_Default:_ `None`

Custom URL to use when connecting to S3, including scheme.
This allows to use a S3-compatible storage service of another provider than AWS.
