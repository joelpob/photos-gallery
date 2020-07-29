#!/bin/bash
if [ $# -eq 0 ]
  then
    echo "sync_aws.sh s3bucketname img-directory thumbnail-directory metadata-file.csv search-dictionary.csv"
    exit 1
fi

# sync with AWS
echo "Syncing with AWS"
aws s3 sync --sse "AES256" --follow-symlinks $3 s3://$2/img/
aws s3 sync --sse "AES256" --follow-symlinks $4 s3://$2/thumbnail/
aws s3 sync --sse "AES256" --follow-symlinks ../js s3://$2/js/
aws s3 sync --sse "AES256" --follow-symlinks ../css s3://$2/css/
aws s3 cp --sse "AES256" ../index.html s3://$2/index.html
aws s3 cp --sse "AES256" $7 s3://$2/photos.csv
aws s3 cp --sse "AES256" $6 s3://$2/search-tokens.csv


