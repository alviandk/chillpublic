$(function() {

    var name, started = false;

    var addItem = function(selector, item) {
        var template = $(selector).find('script[type="text/x-jquery-tmpl"]');
        template.tmpl(item).appendTo(selector);
    };

    var addMessage = function(data) {
        addItem('.messages', data);
        if (bottom) {
            window.scrollBy(0, 10000);
        }
    };

    $('form').submit(function() {
        var value = $('.message').val();
        
        $('#message').val('').focus();
        return false;
    });

    var socket;

    var connected = function() {
        socket.subscribe('room-' + window.room);
        socket.send({room: window.room, action: 'start', name: name});
    };

    var disconnected = function() {
        setTimeout(start, 1000);
    };

    var messaged = function(data) {
        addMessage(data);
    };

    var start = function() {
        socket = new io.Socket();
        socket.connect();
        socket.on('connect', connected);
        socket.on('disconnect', disconnected);
        socket.on('message', messaged);
    };

    start();

});
