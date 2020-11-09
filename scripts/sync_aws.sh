#!/bin/bash
if [ $# -eq 0 ]
  then
    echo "sync_aws.sh s3bucketname img-directory thumbnail-directory metadata-file.csv search-dictionary.csv"
    exit 1
fi

echo "s3bucketname $1"
echo "img-directory $2"
echo "thumbnail-directory $3"
echo "metadata-file $4"
echo "search-dictionary $5"

# sync with AWS
echo "Syncing with AWS"
aws s3 sync --sse "AES256" --follow-symlinks $2 s3://$1/img/
aws s3 sync --sse "AES256" --follow-symlinks $3 s3://$1/thumbnail/
aws s3 sync --sse "AES256" --follow-symlinks ../js s3://$1/js/
aws s3 sync --sse "AES256" --follow-symlinks ../css s3://$1/css/
aws s3 cp --sse "AES256" ../index.html s3://$1/index.html
aws s3 cp --sse "AES256" $4 s3://$1/photos.csv
aws s3 cp --sse "AES256" $5 s3://$1/search-tokens.csv


