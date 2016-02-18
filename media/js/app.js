var ChatApp1 = angular.module('ChatApp1', [
    'SwampDragonServices',
    'ChatControllers'
]);

ChatApp1.config(function($interpolateProvider, $httpProvider) {
    $interpolateProvider.startSymbol('{$').endSymbol('$}');
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});