var http = require('http');
var server = http.createServer().listen(4000, "0.0.0.0");
var io = require('socket.io').listen(server);
var cookie_reader = require('cookie');
var querystring = require('querystring');
var redis = require('redis');
var sub = redis.createClient();
 
//Subscribe to the Redis chat channel
sub.subscribe('chat');

 
io.sockets.on('connection', function (socket) {
    var handshakeData = socket.request;
    var userid = handshakeData._query.user;
    var ticketid = handshakeData._query.ticket;

    socket.on('subscribe', function(room) { 
        console.log('joining room', room);
        socket.join(room); 
    });

    //Grab message from Redis and send to client
    sub.on('message', function(channel, message){
        socket.send(message);
    });
    
    //Client is sending message through socket.io
    socket.on('send_message', function (message) {
        values = querystring.stringify({
            comment: message,
            user: userid,
            ticket: ticketid
        });
        
        var options = {
            host: 'localhost',
            port: '8002',
            path: '/api/post_chat/',
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': values.length
            }
        };

        var post_req = http.request(options, function(res) {
              res.setEncoding('utf8');
              res.on('data', function (chunk) {
                  console.log('Response: ' + chunk);
              });
          });

        post_req.write(values);
        post_req.end();
    });
});