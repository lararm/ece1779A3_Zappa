import boto3

if __name__ == "__main__":

    bucket = 'lambdas3source.people'
    sourceFile = 'happy_2.jpg'
    targetFile = 'TN2.jpg'

    client = boto3.client('rekognition', 'us-east-1')

    response = client.compare_faces(SimilarityThreshold=70,
                                    SourceImage={'S3Object': {'Bucket': bucket, 'Name': sourceFile}},
                                    TargetImage={'S3Object': {'Bucket': bucket, 'Name': targetFile}})
    print(response)
    for faceMatch in response['FaceMatches']:
        position = faceMatch['Face']['BoundingBox']
        confidence = str(faceMatch['Face']['Confidence'])
        print('The face at ' +
              str(position['Left']) + ' ' +
              str(position['Top']) +
              ' matches with ' + confidence + '% confidence')
