# ece1779A3_Zappa
Auto Tagging Photo Album 
<p>This web application was developed AWS serveless and Rekognition API. </p>
<p>Users can upload images and the context of these images is captured and tagged automatically. People profiles can also be added so that the next time 
a photo of a user is uploaded this person is automatically tagged as well</p>

<h3>Application Architecture</h3
<p>The application involved 5 main components:</p>
<ol>
  <li> API Gateway</li>
  <li> Lamda Functions</li>
  <li> S3 Buckets</li>
  <li> DynamoDB</li>
  <li> Amazon Rekognition API</li>
</ol>

<h3>Web Requests</h3>
<ul>
  <li>All HTTP requests are mananged by the API Gateway and Lambda functions</li>
  <li>Image Gallery displays images stored on S3</li>
  <li>Queries for pictures context or profile are handled by the database</li>
</ul>

![alt text](https://github.com/lararm/ece1779A3_Zappa/blob/master/git1.png)

<h3>Upload Images</h3>
<ul>
  <li>Images are uploaded directly to S3. The S3 upload event triggers the rekognition_labeling function to perform the following tasks on each new image:
  </li>
  <li>Call rekognition DetectLabels API to detect labels in S3 object</li>
  <li>Upload Image Tags to database</li>
  <li>Check for Faces</li>
  <li>If a face is found, call recognition Compare_faces</li>
  <li>Add Face Detected Attribute to Image Table</li>
  <li>Update tags table with the profile name</li>
</ul>

![alt text](https://github.com/lararm/ece1779A3_Zappa/blob/master/git2.png)

<h3>Application Usage<h3>
<h4>Logging In</h4>

![alt text](https://github.com/lararm/ece1779A3_Zappa/blob/master/git6.png)

<h4>Image Gallery</h4>

![alt text](https://github.com/lararm/ece1779A3_Zappa/blob/master/git3.png)

<h4>Context Filtering</h4>

![alt text](https://github.com/lararm/ece1779A3_Zappa/blob/master/git4.png)

![alt text](https://github.com/lararm/ece1779A3_Zappa/blob/master/git5.png)




