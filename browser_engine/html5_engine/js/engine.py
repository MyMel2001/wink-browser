"""
JavaScript Engine implementation.
This module provides JavaScript execution capabilities for the browser engine.
"""

import logging
import re
import threading
import json
import time
from typing import Dict, Any, List, Optional, Callable, Union

import dukpy

logger = logging.getLogger(__name__)

class JSEngine:
    """
    JavaScript engine using dukpy for script execution.
    
    This class provides a JavaScript execution environment that can interact
    with the DOM and browser environment.
    """
    
    def __init__(self, window=None):
        """
        Initialize the JavaScript engine.
        
        Args:
            window: Reference to the window/global object
        """
        self.window = window
        
        # Initialize dukpy interpreter
        self.interpreter = dukpy.JSInterpreter()
        
        # Setup standard objects and variables
        self._setup_global_objects()
        
        # Setup polyfills for modern JavaScript features
        self._setup_polyfills()
        
        # JS console implementation
        self.console_output = []
        
        # Event queue
        self.event_queue = []
        
        # Execution state
        self.is_executing = False
        self.is_initialized = True
        
        # Create a separate thread for background evaluation
        self.eval_thread = None

        # Timer management
        self._timers = {}  # timer_id -> (callback_code, type, thread)
        self._timer_counter = 1
        self._timer_lock = threading.Lock()

        # XHR management
        self._xhr_instances = {}  # xhr_id -> {method, url, headers, data, async}
        self._xhr_counter = 1
        self._xhr_lock = threading.Lock()

        logger.info("JavaScript engine initialized")
    
    def _setup_global_objects(self) -> None:
        """Set up standard global objects in the JS environment."""
        # Define the console object
        console_js = """
        var console = {
            log: function() {
                var args = Array.prototype.slice.call(arguments);
                _console_log(JSON.stringify(args));
            },
            error: function() {
                var args = Array.prototype.slice.call(arguments);
                _console_error(JSON.stringify(args));
            },
            warn: function() {
                var args = Array.prototype.slice.call(arguments);
                _console_warn(JSON.stringify(args));
            },
            info: function() {
                var args = Array.prototype.slice.call(arguments);
                _console_info(JSON.stringify(args));
            }
        };
        """
        
        # Define the Event class
        event_js = """
        function Event(type, eventInitDict) {
            this.type = type;
            this.target = null;
            this.currentTarget = null;
            this.eventPhase = 0;
            this.bubbles = eventInitDict ? !!eventInitDict.bubbles : false;
            this.cancelable = eventInitDict ? !!eventInitDict.cancelable : false;
            this.defaultPrevented = false;
            this.isTrusted = false;
            this.timeStamp = Date.now();
            
            this.stopPropagation = function() {
                // Not implemented yet
            };
            
            this.stopImmediatePropagation = function() {
                // Not implemented yet
            };
            
            this.preventDefault = function() {
                if (this.cancelable) {
                    this.defaultPrevented = true;
                }
            };
        }
        """
        
        # Register the Python callbacks for console methods
        self.interpreter.export_function("_console_log", self._console_log)
        self.interpreter.export_function("_console_error", self._console_error)
        self.interpreter.export_function("_console_warn", self._console_warn)
        self.interpreter.export_function("_console_info", self._console_info)
        
        # Initialize the console object
        self.interpreter.evaljs(console_js)
        
        # Initialize the Event class
        self.interpreter.evaljs(event_js)
        
        # Define basic timer functions
        timers_js = """
        var _timers = {};
        var _timerIdCounter = 1;
        var _storedCallbacks = {};  // Store callbacks by ID for execution

        function setTimeout(callback, delay) {
            var timerId = _timerIdCounter++;
            // Store the callback as a string representation for later execution
            var callbackId = 'cb_' + timerId;
            _storedCallbacks[callbackId] = callback;
            _timers[timerId] = {
                callbackId: callbackId,
                type: 'timeout',
                delay: delay,
                createdAt: Date.now()
            };
            _scheduleTimer(timerId, delay);
            return timerId;
        }

        function clearTimeout(timerId) {
            if (_timers[timerId]) {
                var callbackId = _timers[timerId].callbackId;
                if (callbackId && _storedCallbacks[callbackId]) {
                    delete _storedCallbacks[callbackId];
                }
                delete _timers[timerId];
                _clearTimer(timerId);
            }
        }

        function setInterval(callback, delay) {
            var timerId = _timerIdCounter++;
            var callbackId = 'cb_' + timerId;
            _storedCallbacks[callbackId] = callback;
            _timers[timerId] = {
                callbackId: callbackId,
                type: 'interval',
                delay: delay,
                createdAt: Date.now()
            };
            _scheduleTimer(timerId, delay);
            return timerId;
        }

        function clearInterval(timerId) {
            if (_timers[timerId]) {
                var callbackId = _timers[timerId].callbackId;
                if (callbackId && _storedCallbacks[callbackId]) {
                    delete _storedCallbacks[callbackId];
                }
                delete _timers[timerId];
                _clearTimer(timerId);
            }
        }

        // Function to execute a stored callback by ID
        function _executeTimerCallback(callbackId) {
            if (_storedCallbacks[callbackId]) {
                try {
                    if (typeof _storedCallbacks[callbackId] === 'function') {
                        _storedCallbacks[callbackId]();
                    }
                } catch(e) {
                    console.error('Timer callback error:', e);
                }
            }
        }
        """
        
        # Define JSON methods
        json_js = """
        // Duktape has built-in JSON support, but ensure it's properly available
        if (!window.JSON) {
            window.JSON = {
                parse: function(text) {
                    // Use Duktape's built-in JSON parser (safer than eval)
                    return JSON.parse(text);
                },
                stringify: function(obj, replacer, space) {
                    // Use Duktape's built-in JSON stringify
                    return JSON.stringify(obj, replacer, space);
                }
            };
        }
        """
        
        # Create a basic window object
        window_js = """
        var window = this;
        var self = window;
        var location = {
            href: '',
            protocol: 'http:',
            host: '',
            hostname: '',
            port: '',
            pathname: '',
            search: '',
            hash: ''
        };
        var document = {
            title: '',
            readyState: 'loading',
            getElementById: function(id) {
                return null;
            },
            getElementsByTagName: function(tagName) {
                return [];
            },
            getElementsByClassName: function(className) {
                return [];
            },
            querySelector: function(selector) {
                return null;
            },
            querySelectorAll: function(selector) {
                return [];
            },
            createElement: function(tagName) {
                var element = {
                    tagName: tagName.toUpperCase(),
                    style: {},
                    attributes: {},
                    children: [],
                    addEventListener: function(type, listener, options) {
                        // Store event listeners
                        if (!this._eventListeners) this._eventListeners = {};
                        if (!this._eventListeners[type]) this._eventListeners[type] = [];
                        this._eventListeners[type].push(listener);
                    },
                    removeEventListener: function(type, listener) {
                        // Remove event listeners
                        if (!this._eventListeners || !this._eventListeners[type]) return;
                        var index = this._eventListeners[type].indexOf(listener);
                        if (index !== -1) this._eventListeners[type].splice(index, 1);
                    },
                    setAttribute: function(name, value) {
                        this.attributes[name] = value;
                    },
                    getAttribute: function(name) {
                        return this.attributes[name] || null;
                    },
                    appendChild: function(child) {
                        this.children.push(child);
                        return child;
                    }
                };
                return element;
            }
        };
        window.document = document;
        
        // Event listeners storage
        window._eventListeners = {};
        document._eventListeners = {};
        
        // Add addEventListener method to window
        window.addEventListener = function(type, listener, options) {
            if (!window._eventListeners) window._eventListeners = {};
            if (!window._eventListeners[type]) window._eventListeners[type] = [];
            window._eventListeners[type].push(listener);
        };
        
        // Add removeEventListener method to window
        window.removeEventListener = function(type, listener) {
            if (!window._eventListeners || !window._eventListeners[type]) return;
            var index = window._eventListeners[type].indexOf(listener);
            if (index !== -1) window._eventListeners[type].splice(index, 1);
        };
        
        // Add addEventListener method to document
        document.addEventListener = function(type, listener, options) {
            if (!document._eventListeners) document._eventListeners = {};
            if (!document._eventListeners[type]) document._eventListeners[type] = [];
            document._eventListeners[type].push(listener);
        };
        
        // Add removeEventListener method to document
        document.removeEventListener = function(type, listener) {
            if (!document._eventListeners || !document._eventListeners[type]) return;
            var index = document._eventListeners[type].indexOf(listener);
            if (index !== -1) document._eventListeners[type].splice(index, 1);
        };
        
        // Add dispatchEvent method to window
        window.dispatchEvent = function(event) {
            if (event && event.type) {
                // Call the on* handler if it exists
                var handler = window['on' + event.type];
                if (typeof handler === 'function') {
                    handler.call(window, event);
                }
                
                // Call all registered event listeners
                var listeners = window._eventListeners && window._eventListeners[event.type];
                if (listeners) {
                    for (var i = 0; i < listeners.length; i++) {
                        listeners[i].call(window, event);
                    }
                }
                
                return !event.defaultPrevented;
            }
            return true;
        };
        
        // Add dispatchEvent method to document
        document.dispatchEvent = function(event) {
            if (event && event.type) {
                // Call the on* handler if it exists
                var handler = document['on' + event.type];
                if (typeof handler === 'function') {
                    handler.call(document, event);
                }
                
                // Call all registered event listeners
                var listeners = document._eventListeners && document._eventListeners[event.type];
                if (listeners) {
                    for (var i = 0; i < listeners.length; i++) {
                        listeners[i].call(document, event);
                    }
                }
                
                return !event.defaultPrevented;
            }
            return true;
        };
        """
        
        # Create a basic navigator object
        navigator_js = """
        var navigator = {
            userAgent: 'WinkBrowser/1.0 (JavaScript Engine)',
            platform: 'Python',
            language: 'en-US',
            languages: ['en-US', 'en'],
            onLine: true,
            cookieEnabled: true
        };
        window.navigator = navigator;
        """
        
        # Define XMLHttpRequest
        xhr_js = """
        // XHR object registry to allow Python to access XHR instances
        var _xhrObjects = {};

        function XMLHttpRequest() {
            this.readyState = 0;
            this.status = 0;
            this.statusText = '';
            this.responseText = '';
            this.responseXML = null;
            this.response = '';
            this.responseType = '';
            this.onreadystatechange = null;
            this.onload = null;
            this.onerror = null;
            this.upload = {};

            this.open = function(method, url, async) {
                this.method = method;
                this.url = url;
                this.async = async !== false;
                this.readyState = 1;
                if (this.onreadystatechange) this.onreadystatechange();
                _xhr_open(this._id, method, url, this.async);
            };

            this.setRequestHeader = function(header, value) {
                _xhr_setRequestHeader(this._id, header, value);
            };

            this.send = function(data) {
                this.readyState = 2;
                if (this.onreadystatechange) this.onreadystatechange();
                _xhr_send(this._id, data || '');
            };

            this.abort = function() {
                _xhr_abort(this._id);
            };

            this.getAllResponseHeaders = function() {
                return '';
            };

            this.getResponseHeader = function(name) {
                return null;
            };

            this._id = _xhr_create();
            // Register this XHR object in the registry
            _xhrObjects['xhr_' + this._id] = this;
        }
        window.XMLHttpRequest = XMLHttpRequest;
        """

        # Fetch API implementation
        fetch_js = """
        // Fetch API implementation using XMLHttpRequest
        function fetch(url, options) {
            options = options || {};
            var method = options.method || 'GET';
            var headers = options.headers || {};
            var body = options.body || null;
            var signal = options.signal || null;

            return new Promise(function(resolve, reject) {
                var xhr = new XMLHttpRequest();
                xhr.open(method, url, true);

                // Set headers
                if (headers) {
                    for (var key in headers) {
                        if (Object.prototype.hasOwnProperty.call(headers, key)) {
                            xhr.setRequestHeader(key, headers[key]);
                        }
                    }
                }

                xhr.onload = function() {
                    var response = {
                        ok: xhr.status >= 200 && xhr.status < 300,
                        status: xhr.status,
                        statusText: xhr.statusText,
                        url: url,
                        type: 'basic',
                        redirected: false,
                        text: function() {
                            return Promise.resolve(xhr.responseText);
                        },
                        json: function() {
                            try {
                                return Promise.resolve(JSON.parse(xhr.responseText));
                            } catch(e) {
                                return Promise.reject(new SyntaxError('Invalid JSON: ' + e.message));
                            }
                        },
                        blob: function() {
                            return Promise.resolve(new Blob([xhr.responseText]));
                        },
                        arrayBuffer: function() {
                            return Promise.resolve(new ArrayBuffer(0));
                        },
                        clone: function() {
                            return new Response(xhr.responseText, {
                                status: xhr.status,
                                statusText: xhr.statusText
                            });
                        },
                        headers: new Headers()
                    };
                    resolve(response);
                };

                xhr.onerror = function() {
                    reject(new TypeError('Network request failed'));
                };

                xhr.ontimeout = function() {
                    reject(new TypeError('Network request timed out'));
                };

                // Handle abort signal
                if (signal && signal.aborted) {
                    xhr.abort();
                    reject(new DOMException('The user aborted a request.', 'AbortError'));
                    return;
                }

                xhr.send(body);
            });
        }
        window.fetch = fetch;

        // Headers interface
        function Headers(init) {
            this._headers = {};
            if (init) {
                if (Array.isArray(init)) {
                    for (var i = 0; i < init.length; i++) {
                        this.append(init[i][0], init[i][1]);
                    }
                } else if (typeof init === 'object') {
                    for (var key in init) {
                        if (Object.prototype.hasOwnProperty.call(init, key)) {
                            this.append(key, init[key]);
                        }
                    }
                }
            }
        }
        Headers.prototype.append = function(name, value) {
            name = String(name).toLowerCase();
            if (!this._headers[name]) this._headers[name] = [];
            this._headers[name].push(String(value));
        };
        Headers.prototype.delete = function(name) {
            delete this._headers[String(name).toLowerCase()];
        };
        Headers.prototype.get = function(name) {
            var values = this._headers[String(name).toLowerCase()];
            return values ? values[0] : null;
        };
        Headers.prototype.getAll = function(name) {
            return this._headers[String(name).toLowerCase()] || [];
        };
        Headers.prototype.has = function(name) {
            return String(name).toLowerCase() in this._headers;
        };
        Headers.prototype.set = function(name, value) {
            name = String(name).toLowerCase();
            this._headers[name] = [String(value)];
        };
        Headers.prototype.keys = function() {
            return Object.keys(this._headers);
        };
        Headers.prototype.values = function() {
            var self = this;
            return Object.keys(this._headers).map(function(k) { return self._headers[k][0]; });
        };
        Headers.prototype.entries = function() {
            var self = this;
            return Object.keys(this._headers).map(function(k) { return [k, self._headers[k][0]]; });
        };
        window.Headers = Headers;

        // Response interface
        function Response(body, init) {
            init = init || {};
            this.body = body;
            this.bodyUsed = false;
            this.status = init.status !== undefined ? init.status : 200;
            this.statusText = init.statusText || '';
            this.ok = this.status >= 200 && this.status < 300;
            this.redirected = init.redirected || false;
            this.type = init.type || 'basic';
            this.url = init.url || '';
            this.headers = init.headers instanceof Headers ? init.headers : new Headers(init.headers);
        }
        Response.prototype.text = function() {
            this.bodyUsed = true;
            return Promise.resolve(this.body);
        };
        Response.prototype.json = function() {
            this.bodyUsed = true;
            return Promise.resolve(JSON.parse(this.body));
        };
        Response.prototype.blob = function() {
            this.bodyUsed = true;
            return Promise.resolve(new Blob([this.body]));
        };
        Response.prototype.clone = function() {
            return new Response(this.body, {
                status: this.status,
                statusText: this.statusText,
                headers: this.headers,
                url: this.url
            });
        };
        Response.error = function() {
            return new Response(null, { status: 0, statusText: '', type: 'error' });
        };
        Response.redirect = function(url, status) {
            status = status || 302;
            return new Response(null, { status: status, headers: { Location: url } });
        };
        window.Response = Response;

        // Request interface
        function Request(input, init) {
            init = init || {};
            if (typeof input === 'string') {
                this.url = input;
            } else if (input instanceof Request) {
                this.url = input.url;
                this.method = input.method;
                this.headers = input.headers;
                this.body = input.body;
            } else {
                this.url = String(input);
            }
            this.method = init.method || 'GET';
            this.headers = init.headers instanceof Headers ? init.headers : new Headers(init.headers);
            this.body = init.body || null;
            this.credentials = init.credentials || 'same-origin';
            this.cache = init.cache || 'default';
            this.redirect = init.redirect || 'follow';
            this.referrer = init.referrer || '';
            this.mode = init.mode || 'cors';
        }
        Request.prototype.text = function() {
            return Promise.resolve(this.body || '');
        };
        Request.prototype.json = function() {
            return Promise.resolve(JSON.parse(this.body || '{}'));
        };
        Request.prototype.clone = function() {
            return new Request(this.url, {
                method: this.method,
                headers: this.headers,
                body: this.body
            });
        };
        window.Request = Request;

        // Blob interface (simplified)
        function Blob(parts, options) {
            this.parts = parts || [];
            this.size = 0;
            for (var i = 0; i < this.parts.length; i++) {
                var part = this.parts[i];
                this.size += typeof part === 'string' ? part.length : (part.size || 0);
            }
            this.type = options && options.type ? options.type : '';
        }
        Blob.prototype.slice = function(start, end, type) {
            return new Blob(this.parts.slice(start, end), { type: type || this.type });
        };
        Blob.prototype.text = function() {
            return Promise.resolve(this.parts.join(''));
        };
        Blob.prototype.arrayBuffer = function() {
            return Promise.resolve(new ArrayBuffer(this.size));
        };
        window.Blob = Blob;

        // ArrayBuffer (stub)
        function ArrayBuffer(length) {
            this.length = length;
            this.byteLength = length;
        }
        window.ArrayBuffer = ArrayBuffer;

        // AbortController and AbortSignal
        function AbortController() {
            this.signal = new AbortSignal();
        }
        AbortController.prototype.abort = function() {
            this.signal._aborted = true;
        };
        window.AbortController = AbortController;

        function AbortSignal() {
            this._aborted = false;
        }
        Object.defineProperty(AbortSignal.prototype, 'aborted', {
            get: function() { return this._aborted; }
        });
        window.AbortSignal = AbortSignal;

        // URL and URLSearchParams (basic implementation)
        function URL(url, base) {
            if (base) {
                url = base + (url.startsWith('/') ? '' : '/') + url;
            }
            this.href = url;
            this.protocol = '';
            this.host = '';
            this.hostname = '';
            this.port = '';
            this.pathname = '';
            this.search = '';
            this.hash = '';

            // Simple parsing
            var match = url.match(/^(https?:)\\/\\/([^\\/\\?#]+)(\\/[^?#]*)?(\\?[^#]*)?(#.*)?$/);
            if (match) {
                this.protocol = match[1];
                this.host = match[2];
                this.hostname = match[2].split(':')[0];
                this.port = match[2].split(':')[1] || '';
                this.pathname = match[3] || '/';
                this.search = match[4] || '';
                this.hash = match[5] || '';
            }
        }
        URL.prototype.toString = function() { return this.href; };
        window.URL = URL;

        function URLSearchParams(init) {
            this.params = {};
            if (typeof init === 'string') {
                var pairs = init.replace(/^\\?/, '').split('&');
                for (var i = 0; i < pairs.length; i++) {
                    var pair = pairs[i].split('=');
                    if (pair[0]) {
                        this.params[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
                    }
                }
            }
        }
        URLSearchParams.prototype.append = function(name, value) {
            this.params[name] = value;
        };
        URLSearchParams.prototype.get = function(name) {
            return this.params[name] || null;
        };
        URLSearchParams.prototype.toString = function() {
            var pairs = [];
            for (var key in this.params) {
                pairs.push(encodeURIComponent(key) + '=' + encodeURIComponent(this.params[key]));
            }
            return pairs.join('&');
        };
        window.URLSearchParams = URLSearchParams;
        """

        # Execute all the setup code
        self.interpreter.evaljs(window_js)
        self.interpreter.evaljs(navigator_js)
        self.interpreter.evaljs(timers_js)
        self.interpreter.evaljs(json_js)
        self.interpreter.evaljs(xhr_js)
        self.interpreter.evaljs(fetch_js)  # Add fetch API

        # Register Python callbacks for JS functions
        self.interpreter.export_function('_scheduleTimer', self._schedule_timer)
        self.interpreter.export_function('_clearTimer', self._clear_timer)
        self.interpreter.export_function('_xhr_create', self._xhr_create)
        self.interpreter.export_function('_xhr_open', self._xhr_open)
        self.interpreter.export_function('_xhr_setRequestHeader', self._xhr_set_request_header)
        self.interpreter.export_function('_xhr_send', self._xhr_send)
        self.interpreter.export_function('_xhr_abort', self._xhr_abort)
        
        # Mark as initialized
        self.is_initialized = True
    
    def _setup_polyfills(self) -> None:
        """Set up polyfills for modern JavaScript features not supported by dukpy."""
        # Polyfills for ES6+ features
        polyfills_js = """
        // Array polyfills
        if (!Array.prototype.find) {
            Array.prototype.find = function(predicate) {
                if (this == null) {
                    throw new TypeError('Array.prototype.find called on null or undefined');
                }
                if (typeof predicate !== 'function') {
                    throw new TypeError('predicate must be a function');
                }
                var list = Object(this);
                var length = list.length >>> 0;
                var thisArg = arguments[1];
                
                for (var i = 0; i < length; i++) {
                    var value = list[i];
                    if (predicate.call(thisArg, value, i, list)) {
                        return value;
                    }
                }
                return undefined;
            };
        }

        if (!Array.prototype.findIndex) {
            Array.prototype.findIndex = function(predicate) {
                if (this == null) {
                    throw new TypeError('Array.prototype.findIndex called on null or undefined');
                }
                if (typeof predicate !== 'function') {
                    throw new TypeError('predicate must be a function');
                }
                var list = Object(this);
                var length = list.length >>> 0;
                var thisArg = arguments[1];
                
                for (var i = 0; i < length; i++) {
                    if (predicate.call(thisArg, list[i], i, list)) {
                        return i;
                    }
                }
                return -1;
            };
        }

        if (!Array.prototype.includes) {
            Array.prototype.includes = function(searchElement, fromIndex) {
                if (this == null) {
                    throw new TypeError('Array.prototype.includes called on null or undefined');
                }
                
                var O = Object(this);
                var len = parseInt(O.length) || 0;
                if (len === 0) {
                    return false;
                }
                
                var n = parseInt(fromIndex) || 0;
                var k;
                
                if (n >= 0) {
                    k = n;
                } else {
                    k = len + n;
                    if (k < 0) {
                        k = 0;
                    }
                }
                
                while (k < len) {
                    var currentElement = O[k];
                    if (searchElement === currentElement || 
                        (searchElement !== searchElement && currentElement !== currentElement)) {
                        return true;
                    }
                    k++;
                }
                
                return false;
            };
        }

        // String polyfills
        if (!String.prototype.startsWith) {
            String.prototype.startsWith = function(searchString, position) {
                position = position || 0;
                return this.substr(position, searchString.length) === searchString;
            };
        }

        if (!String.prototype.endsWith) {
            String.prototype.endsWith = function(searchString, position) {
                var subjectString = this.toString();
                if (typeof position !== 'number' || !isFinite(position) || 
                    Math.floor(position) !== position || position > subjectString.length) {
                    position = subjectString.length;
                }
                position -= searchString.length;
                var lastIndex = subjectString.indexOf(searchString, position);
                return lastIndex !== -1 && lastIndex === position;
            };
        }

        if (!String.prototype.includes) {
            String.prototype.includes = function(search, start) {
                if (typeof start !== 'number') {
                    start = 0;
                }
                if (start + search.length > this.length) {
                    return false;
                } else {
                    return this.indexOf(search, start) !== -1;
                }
            };
        }

        if (!String.prototype.repeat) {
            String.prototype.repeat = function(count) {
                if (this == null) {
                    throw new TypeError('String.prototype.repeat called on null or undefined');
                }
                
                var string = String(this);
                count = +count;
                
                if (count !== count) {
                    count = 0;
                }
                
                if (count < 0 || count === Infinity) {
                    throw new RangeError('Invalid count value');
                }
                
                count = Math.floor(count);
                if (string.length === 0 || count === 0) {
                    return '';
                }
                
                var result = '';
                while (count) {
                    if (count & 1) {
                        result += string;
                    }
                    if (count >>= 1) {
                        string += string;
                    }
                }
                return result;
            };
        }

        // Object polyfills
        if (!Object.assign) {
            Object.assign = function(target) {
                if (target == null) {
                    throw new TypeError('Cannot convert undefined or null to object');
                }
                
                var to = Object(target);
                
                for (var index = 1; index < arguments.length; index++) {
                    var nextSource = arguments[index];
                    
                    if (nextSource != null) {
                        for (var nextKey in nextSource) {
                            if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
                                to[nextKey] = nextSource[nextKey];
                            }
                        }
                    }
                }
                
                return to;
            };
        }

        // Promise polyfill for basic promise support
        if (typeof Promise === 'undefined') {
            window.Promise = function(executor) {
                var self = this;
                self.status = 'pending';
                self.value = undefined;
                self.reason = undefined;
                self.onFulfilledCallbacks = [];
                self.onRejectedCallbacks = [];
                
                function resolve(value) {
                    if (self.status === 'pending') {
                        self.status = 'fulfilled';
                        self.value = value;
                        for (var i = 0; i < self.onFulfilledCallbacks.length; i++) {
                            self.onFulfilledCallbacks[i](value);
                        }
                    }
                }
                
                function reject(reason) {
                    if (self.status === 'pending') {
                        self.status = 'rejected';
                        self.reason = reason;
                        for (var i = 0; i < self.onRejectedCallbacks.length; i++) {
                            self.onRejectedCallbacks[i](reason);
                        }
                    }
                }
                
                try {
                    executor(resolve, reject);
                } catch(e) {
                    reject(e);
                }
            };
            
            Promise.prototype.then = function(onFulfilled, onRejected) {
                var self = this;
                var promise2 = new Promise(function(resolve, reject) {
                    function handleFulfilled(value) {
                        if (typeof onFulfilled === 'function') {
                            try {
                                var x = onFulfilled(value);
                                resolve(x);
                            } catch(e) {
                                reject(e);
                            }
                        } else {
                            resolve(value);
                        }
                    }
                    
                    function handleRejected(reason) {
                        if (typeof onRejected === 'function') {
                            try {
                                var x = onRejected(reason);
                                resolve(x);
                            } catch(e) {
                                reject(e);
                            }
                        } else {
                            reject(reason);
                        }
                    }
                    
                    if (self.status === 'fulfilled') {
                        setTimeout(function() {
                            handleFulfilled(self.value);
                        }, 0);
                    } else if (self.status === 'rejected') {
                        setTimeout(function() {
                            handleRejected(self.reason);
                        }, 0);
                    } else if (self.status === 'pending') {
                        self.onFulfilledCallbacks.push(function(value) {
                            setTimeout(function() {
                                handleFulfilled(value);
                            }, 0);
                        });
                        self.onRejectedCallbacks.push(function(reason) {
                            setTimeout(function() {
                                handleRejected(reason);
                            }, 0);
                        });
                    }
                });
                
                return promise2;
            };
            
            Promise.prototype.catch = function(onRejected) {
                return this.then(null, onRejected);
            };

            Promise.prototype.finally = function(onFinally) {
                return this.then(
                    function(value) {
                        if (typeof onFinally === 'function') onFinally();
                        return value;
                    },
                    function(reason) {
                        if (typeof onFinally === 'function') onFinally();
                        throw reason;
                    }
                );
            };

            Promise.resolve = function(value) {
                return new Promise(function(resolve) {
                    resolve(value);
                });
            };

            Promise.reject = function(reason) {
                return new Promise(function(resolve, reject) {
                    reject(reason);
                });
            };

            Promise.all = function(promises) {
                return new Promise(function(resolve, reject) {
                    if (!Array.isArray(promises)) {
                        return reject(new TypeError('Promise.all accepts an array'));
                    }

                    var results = [];
                    var remaining = promises.length;

                    if (remaining === 0) {
                        return resolve(results);
                    }

                    function resolvePromise(i, value) {
                        results[i] = value;
                        remaining--;
                        if (remaining === 0) {
                            resolve(results);
                        }
                    }

                    for (var i = 0; i < promises.length; i++) {
                        (function(i) {
                            var promise = promises[i];
                            if (promise && typeof promise.then === 'function') {
                                promise.then(
                                    function(value) {
                                        resolvePromise(i, value);
                                    },
                                    function(reason) {
                                        reject(reason);
                                    }
                                );
                            } else {
                                resolvePromise(i, promise);
                            }
                        })(i);
                    }
                });
            };

            Promise.race = function(promises) {
                return new Promise(function(resolve, reject) {
                    if (!Array.isArray(promises)) {
                        return reject(new TypeError('Promise.race accepts an array'));
                    }

                    for (var i = 0; i < promises.length; i++) {
                        var promise = promises[i];
                        if (promise && typeof promise.then === 'function') {
                            promise.then(resolve, reject);
                        } else {
                            resolve(promise);
                            return;
                        }
                    }
                });
            };

            Promise.allSettled = function(promises) {
                return new Promise(function(resolve) {
                    if (!Array.isArray(promises)) {
                        return resolve([]);
                    }

                    var results = [];
                    var remaining = promises.length;

                    if (remaining === 0) {
                        return resolve(results);
                    }

                    function settlePromise(i, status, value) {
                        results[i] = { status: status, value: value };
                        remaining--;
                        if (remaining === 0) {
                            resolve(results);
                        }
                    }

                    for (var i = 0; i < promises.length; i++) {
                        (function(i) {
                            var promise = promises[i];
                            if (promise && typeof promise.then === 'function') {
                                promise.then(
                                    function(value) { settlePromise(i, 'fulfilled', value); },
                                    function(reason) { settlePromise(i, 'rejected', reason); }
                                );
                            } else {
                                settlePromise(i, 'fulfilled', promise);
                            }
                        })(i);
                    }
                });
            };

            Promise.any = function(promises) {
                return new Promise(function(resolve, reject) {
                    if (!Array.isArray(promises)) {
                        return reject(new TypeError('Promise.any accepts an array'));
                    }

                    var errors = [];
                    var remaining = promises.length;

                    if (remaining === 0) {
                        return reject(new AggregateError([], 'All promises were rejected'));
                    }

                    for (var i = 0; i < promises.length; i++) {
                        (function(i) {
                            var promise = promises[i];
                            if (promise && typeof promise.then === 'function') {
                                promise.then(resolve, function(reason) {
                                    errors[i] = reason;
                                    remaining--;
                                    if (remaining === 0) {
                                        reject(new AggregateError(errors, 'All promises were rejected'));
                                    }
                                });
                            } else {
                                resolve(promise);
                            }
                        })(i);
                    }
                });
            };
        }
        """
        
        try:
            # Add the polyfills to the JS environment
            self.interpreter.evaljs(polyfills_js)
            logger.debug("JavaScript polyfills initialized")
        except Exception as e:
            logger.error(f"Error setting up JavaScript polyfills: {e}")
    
    def _apply_polyfill_middleware(self, js_code: str) -> str:
        """
        Apply polyfill middleware to JavaScript code.
        This function checks the code for unsupported features and wraps
        them with compatible alternatives.
        
        Args:
            js_code: The JavaScript code to process
            
        Returns:
            Processed JavaScript code with polyfills applied as needed
        """
        if not js_code:
            return js_code
        
        # Wrap the code in a try-catch block to capture and log errors
        wrapped_code = """
        try {
            %s
        } catch (e) {
            console.error('JavaScript error: ' + e.message);
        }
        """ % js_code
        
        # Check for modern array methods and ensure they're polyfilled
        array_methods = ['find', 'findIndex', 'includes', 'from', 'of']
        for method in array_methods:
            if f"Array.prototype.{method}" in js_code or f".{method}(" in js_code:
                logger.debug(f"Detected possible use of Array.{method} - polyfill will be applied")
        
        # Check for modern string methods
        string_methods = ['startsWith', 'endsWith', 'includes', 'repeat', 'padStart', 'padEnd']
        for method in string_methods:
            if f"String.prototype.{method}" in js_code or f".{method}(" in js_code:
                logger.debug(f"Detected possible use of String.{method} - polyfill will be applied")
        
        # Check for Promise usage
        if "new Promise" in js_code or "Promise." in js_code:
            logger.debug("Detected possible use of Promises - polyfill will be applied")
        
        # Check for Object.assign
        if "Object.assign" in js_code:
            logger.debug("Detected possible use of Object.assign - polyfill will be applied")
        
        return wrapped_code
    
    def evaluate(self, js_code: str, async_eval: bool = False) -> Any:
        """
        Evaluate JavaScript code.
        
        Args:
            js_code: JavaScript code to evaluate
            async_eval: Whether to evaluate asynchronously
            
        Returns:
            The result of the evaluation, or None if async_eval is True
        """
        if not self.is_initialized:
            logger.warning("JS engine not initialized, initializing now")
            self._setup_global_objects()
            self._setup_polyfills()
            self.is_initialized = True
        
        # Apply polyfill middleware to the code
        processed_code = self._apply_polyfill_middleware(js_code)
        
        if async_eval:
            if self.eval_thread and self.eval_thread.is_alive():
                logger.warning("Another JavaScript evaluation is already running")
                return None
            
            self.eval_thread = threading.Thread(
                target=self._evaluate_in_thread, 
                args=(processed_code,)
            )
            self.eval_thread.daemon = True
            self.eval_thread.start()
            return None
        else:
            return self._evaluate_sync(processed_code)
    
    def _console_log(self, message: str) -> None:
        """
        Handle console.log calls from JavaScript.
        
        Args:
            message: The console message in JSON format
        """
        try:
            args = json.loads(message)
            log_message = ' '.join(str(arg) for arg in args)
            logger.info(f"JS console.log: {log_message}")
            self.console_output.append(('log', log_message))
        except Exception as e:
            logger.error(f"Error in console.log: {e}")
    
    def _console_error(self, message: str) -> None:
        """
        Handle console.error calls from JavaScript.
        
        Args:
            message: The console message in JSON format
        """
        try:
            args = json.loads(message)
            log_message = ' '.join(str(arg) for arg in args)
            logger.error(f"JS console.error: {log_message}")
            self.console_output.append(('error', log_message))
        except Exception as e:
            logger.error(f"Error in console.error: {e}")
    
    def _console_warn(self, message: str) -> None:
        """
        Handle console.warn calls from JavaScript.
        
        Args:
            message: The console message in JSON format
        """
        try:
            args = json.loads(message)
            log_message = ' '.join(str(arg) for arg in args)
            logger.warning(f"JS console.warn: {log_message}")
            self.console_output.append(('warn', log_message))
        except Exception as e:
            logger.error(f"Error in console.warn: {e}")
    
    def _console_info(self, message: str) -> None:
        """
        Handle console.info calls from JavaScript.
        
        Args:
            message: The console message in JSON format
        """
        try:
            args = json.loads(message)
            log_message = ' '.join(str(arg) for arg in args)
            logger.info(f"JS console.info: {log_message}")
            self.console_output.append(('info', log_message))
        except Exception as e:
            logger.error(f"Error in console.info: {e}")
    
    def _schedule_timer(self, timer_id: int, delay: int) -> None:
        """
        Schedule a timer for execution.

        Args:
            timer_id: The timer ID
            delay: Delay in milliseconds
        """
        delay_seconds = max(0, delay / 1000.0)  # Convert to seconds, ensure non-negative

        def execute_timer():
            with self._timer_lock:
                if timer_id not in self._timers:
                    return
                timer_info = self._timers[timer_id]
                callback_id = timer_info.get('callbackId', f'cb_{timer_id}')
                timer_type = timer_info.get('type', 'timeout')

            try:
                # Execute the callback using the stored callback ID in JS
                self.interpreter.evaljs(f"_executeTimerCallback('{callback_id}')")
                logger.debug(f"Timer {timer_id} callback executed")

                # If it's an interval, reschedule it
                if timer_type == 'interval':
                    with self._timer_lock:
                        if timer_id in self._timers:
                            timer_info['thread'] = threading.Timer(delay_seconds, execute_timer)
                            timer_info['thread'].daemon = True
                            timer_info['thread'].start()
            except Exception as e:
                logger.error(f"Error executing timer {timer_id}: {e}")

        # Start the timer
        timer_thread = threading.Timer(delay_seconds, execute_timer)
        timer_thread.daemon = True
        timer_thread.start()

        with self._timer_lock:
            self._timers[timer_id] = {
                'thread': timer_thread,
                'type': 'timeout',  # Will be updated if interval
                'callbackId': f'cb_{timer_id}'
            }

        logger.debug(f"Scheduled timer {timer_id} with delay {delay}ms")
    
    def _clear_timer(self, timer_id: int) -> None:
        """
        Clear a scheduled timer.

        Args:
            timer_id: The timer ID to clear
        """
        with self._timer_lock:
            if timer_id in self._timers:
                timer_info = self._timers[timer_id]
                if 'thread' in timer_info and timer_info['thread']:
                    timer_info['thread'].cancel()
                del self._timers[timer_id]
        logger.debug(f"Cleared timer {timer_id}")

    def _xhr_create(self) -> int:
        """
        Create a new XMLHttpRequest instance.

        Returns:
            ID for the new XHR instance
        """
        with self._xhr_lock:
            xhr_id = self._xhr_counter
            self._xhr_counter += 1
            self._xhr_instances[xhr_id] = {
                'method': None,
                'url': None,
                'headers': {},
                'data': None,
                'async': True
            }
        logger.debug(f"Created XHR instance with ID {xhr_id}")
        return xhr_id

    def _xhr_open(self, xhr_id: int, method: str, url: str, async_flag: bool) -> None:
        """
        Handle XMLHttpRequest.open.

        Args:
            xhr_id: The XHR instance ID
            method: HTTP method
            url: Request URL
            async_flag: Whether the request is asynchronous
        """
        with self._xhr_lock:
            if xhr_id in self._xhr_instances:
                self._xhr_instances[xhr_id]['method'] = method
                self._xhr_instances[xhr_id]['url'] = url
                self._xhr_instances[xhr_id]['async'] = async_flag
        logger.debug(f"XHR {xhr_id} open: {method} {url} (async: {async_flag})")

    def _xhr_set_request_header(self, xhr_id: int, header: str, value: str) -> None:
        """
        Handle XMLHttpRequest.setRequestHeader.

        Args:
            xhr_id: The XHR instance ID
            header: Header name
            value: Header value
        """
        with self._xhr_lock:
            if xhr_id in self._xhr_instances:
                self._xhr_instances[xhr_id]['headers'][header] = value
        logger.debug(f"XHR {xhr_id} setRequestHeader: {header}={value}")

    def _xhr_send(self, xhr_id: int, data: str) -> None:
        """
        Handle XMLHttpRequest.send.

        Args:
            xhr_id: The XHR instance ID
            data: Request data
        """
        with self._xhr_lock:
            if xhr_id not in self._xhr_instances:
                logger.warning(f"XHR {xhr_id} not found")
                return
            xhr_info = self._xhr_instances[xhr_id].copy()
            xhr_info['data'] = data

        logger.debug(f"XHR {xhr_id} send: {data}")

        # Make the actual HTTP request in a separate thread
        def perform_request():
            try:
                import urllib.request
                url = xhr_info.get('url', '')
                method = xhr_info.get('method', 'GET').upper()
                headers = xhr_info.get('headers', {})
                request_data = xhr_info.get('data')

                # Create request
                req = urllib.request.Request(url, method=method)

                # Add headers
                for header, value in headers.items():
                    req.add_header(header, value)

                # Add data for POST/PUT requests
                if request_data and method in ('POST', 'PUT', 'PATCH'):
                    req.data = request_data.encode('utf-8')

                # Perform request
                try:
                    with urllib.request.urlopen(req, timeout=30) as response:
                        response_text = response.read().decode('utf-8', errors='replace')
                        status = response.status
                        self._complete_xhr(xhr_id, status, response_text)
                except urllib.error.HTTPError as e:
                    response_text = e.read().decode('utf-8', errors='replace')
                    self._complete_xhr(xhr_id, e.code, response_text)
                except urllib.error.URLError as e:
                    self._complete_xhr(xhr_id, 0, str(e.reason))
                except Exception as e:
                    self._complete_xhr(xhr_id, 0, str(e))

            except Exception as e:
                logger.error(f"XHR {xhr_id} request error: {e}")
                self._complete_xhr(xhr_id, 0, str(e))

        # Start request in background thread
        thread = threading.Thread(target=perform_request, daemon=True)
        thread.start()

    def _complete_xhr(self, xhr_id: int, status: int, response_text: str) -> None:
        """
        Complete an XHR request with the response.

        Args:
            xhr_id: The XHR instance ID
            status: HTTP status code
            response_text: Response text
        """
        try:
            # Escape the response text for JS
            escaped_response = response_text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')

            # Update the XHR object in JS and trigger callbacks
            self.interpreter.evaljs(f"""
            (function() {{
                if (typeof _xhrObjects !== 'undefined' && _xhrObjects['xhr_{xhr_id}']) {{
                    var xhr = _xhrObjects['xhr_{xhr_id}'];
                    xhr.readyState = 4;
                    xhr.status = {status};
                    xhr.statusText = '{status} OK';
                    xhr.responseText = "{escaped_response}";
                    xhr.response = xhr.responseText;
                    if (xhr.onreadystatechange) xhr.onreadystatechange();
                    if (xhr.onload) xhr.onload();
                }}
            }})();
            """)
            logger.debug(f"XHR {xhr_id} completed with status {status}")
        except Exception as e:
            logger.error(f"Error completing XHR {xhr_id}: {e}")

    def _xhr_abort(self, xhr_id: int) -> None:
        """
        Handle XMLHttpRequest.abort.

        Args:
            xhr_id: The XHR instance ID
        """
        with self._xhr_lock:
            if xhr_id in self._xhr_instances:
                del self._xhr_instances[xhr_id]
        logger.debug(f"XHR {xhr_id} abort")
    
    def _evaluate_in_thread(self, code: str) -> None:
        """
        Evaluate JavaScript code in a separate thread.
        
        Args:
            code: JavaScript code to evaluate
        """
        try:
            self.is_executing = True
            result = self.interpreter.evaljs(code)
            logger.debug(f"Async JS evaluation result: {result}")
        except Exception as e:
            logger.error(f"Error in async JS evaluation: {e}")
        finally:
            self.is_executing = False
    
    def _evaluate_sync(self, code: str) -> Any:
        """
        Evaluate JavaScript code synchronously.
        
        Args:
            code: JavaScript code to evaluate
            
        Returns:
            The result of the evaluation
        """
        try:
            self.is_executing = True
            # Catch syntax errors before evaluation
            try:
                result = self.interpreter.evaljs(code)
                return result
            except dukpy.JSRuntimeError as js_error:
                # More informative error handling for JavaScript runtime errors
                error_msg = str(js_error)
                logger.error(f"Error in JS evaluation: {error_msg}")
                
                # Attempt to extract line number from error message
                line_match = re.search(r'line (\d+)', error_msg)
                if line_match:
                    line_num = int(line_match.group(1))
                    code_lines = code.split('\n')
                    
                    # Show context around the error
                    start_line = max(0, line_num - 3)
                    end_line = min(len(code_lines), line_num + 2)
                    
                    context = "\n".join(f"{i+1}: {line}" for i, line in enumerate(code_lines[start_line:end_line]))
                    logger.error(f"Error context:\n{context}")
                
                return None
        except Exception as e:
            logger.error(f"Error in JS evaluation: {e}")
            return None
        finally:
            self.is_executing = False
    
    def setup_document(self, document) -> None:
        """
        Set up the JavaScript document object to reflect the DOM.

        Args:
            document: The HTML document
        """
        if not document:
            logger.warning("Cannot setup document: document is None")
            return

        # Use the DOM bridge for proper DOM-JS integration
        from .dom_bridge import DOMBridge

        if not hasattr(self, '_dom_bridge'):
            self._dom_bridge = DOMBridge(self.interpreter, document)
            self._dom_bridge.register_python_callbacks()

        self._dom_bridge.setup_document(document)

        # Dispatch DOMContentLoaded event
        self.interpreter.evaljs("""
        if (typeof window.addEventListener === 'function') {
            var event = { type: 'DOMContentLoaded' };
            window.dispatchEvent(event);
        }
        document.readyState = "complete";
        """)
    
    def execute_scripts(self, document) -> None:
        """
        Execute all script tags in the document.
        
        Args:
            document: The HTML document
        """
        if not document:
            logger.warning("Cannot execute scripts: document is None")
            return
        
        # Find all script elements
        script_elements = self._find_script_elements(document)
        
        for script in script_elements:
            # Skip if script has a 'type' attribute that isn't JavaScript
            script_type = script.get_attribute('type') if hasattr(script, 'get_attribute') else None
            if script_type and script_type.lower() not in ('text/javascript', 'application/javascript', ''):
                continue
                
            # Check if it's an external script
            src = script.get_attribute('src') if hasattr(script, 'get_attribute') else None
            if src:
                logger.info(f"Would load external script from: {src}")
                
                # Check if we have a window and can request the script
                if self.window and hasattr(self.window, 'document') and hasattr(self.window.document, 'network_manager'):
                    try:
                        # Only attempt to load scripts from the same origin or if CORS allows
                        base_url = self.window.document.url if hasattr(self.window.document, 'url') else None
                        
                        if base_url:
                            # Resolve relative URLs
                            if not src.startswith(('http://', 'https://')):
                                from urllib.parse import urljoin
                                full_src_url = urljoin(base_url, src)
                            else:
                                full_src_url = src
                                
                            logger.debug(f"Attempting to load script from: {full_src_url}")
                            
                            # Use the network manager to fetch the script
                            # This is simplified - in a real implementation you'd check CORS,
                            # handle errors, etc.
                            script_content = self.window.document.network_manager.fetch(full_src_url)
                            
                            if script_content:
                                logger.info(f"Successfully loaded script from {src}")
                                sanitized_content = self._sanitize_script_content(script_content)
                                try:
                                    self.evaluate(sanitized_content)
                                except Exception as e:
                                    logger.error(f"Error in JS evaluation: {e}")
                            else:
                                logger.warning(f"Failed to load script from {src}")
                    except Exception as e:
                        logger.error(f"Error loading external script {src}: {e}")
                
                continue
                
            # Execute inline script - first check for script_content property, then fallback to text_content
            if hasattr(script, 'script_content') and script.script_content:
                try:
                    logger.info("Executing inline script")
                    # Clean up the script content to avoid unterminated statement errors
                    script_content = self._sanitize_script_content(script.script_content)
                    self.evaluate(script_content)
                except Exception as e:
                    logger.error(f"Error in JS evaluation: {e}")
            elif hasattr(script, 'text_content') and script.text_content:
                try:
                    logger.info("Executing inline script from text_content")
                    # Clean up the script content to avoid unterminated statement errors
                    script_content = self._sanitize_script_content(script.text_content)
                    self.evaluate(script_content)
                except Exception as e:
                    logger.error(f"Error in JS evaluation: {e}")
    
    def _sanitize_script_content(self, content: str) -> str:
        """
        Sanitize script content to avoid common errors.
        
        Args:
            content: The script content to sanitize
            
        Returns:
            Sanitized script content
        """
        if not content:
            return ""
            
        # Remove HTML comments that might be in the script
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # State machine for string handling
        result = []
        state = 'normal'  # States: normal, single_quote, double_quote, backtick
        escaped = False
        last_char = None
        
        for char in content:
            if state == 'normal':
                if char == "'" and not escaped:
                    state = 'single_quote'
                elif char == '"' and not escaped:
                    state = 'double_quote'
                elif char == '`' and not escaped:
                    state = 'backtick'
                escaped = char == '\\'
                result.append(char)
            elif state == 'single_quote':
                if char == "'" and not escaped:
                    state = 'normal'
                escaped = char == '\\' and not escaped
                result.append(char)
            elif state == 'double_quote':
                if char == '"' and not escaped:
                    state = 'normal'
                escaped = char == '\\' and not escaped
                result.append(char)
            elif state == 'backtick':
                if char == '`' and not escaped:
                    state = 'normal'
                escaped = char == '\\' and not escaped
                result.append(char)
            last_char = char
            
        # Close any unclosed strings
        if state == 'single_quote':
            result.append("'")
        elif state == 'double_quote':
            result.append('"')
        elif state == 'backtick':
            result.append('`')
            
        content = ''.join(result)
        
        # Special fix for DuckDuckGo scripts that have unterminated if statements
        if "duckduckgo.com" in content or "duck.com" in content:
            # If we find an if statement without closing braces, add them
            if re.search(r'if\s*\([^{]*\)\s*{[^}]*$', content) or \
               re.search(r'if\s*\(typeof console !== \'undefined\'\s*&&\s*console\.error\)', content):
                content += "\nconsole.error(e); }"
        
        # Ensure balanced braces and parentheses
        braces_count = content.count('{') - content.count('}')
        if braces_count > 0:
            content += '}' * braces_count
        
        parens_count = content.count('(') - content.count(')')
        if parens_count > 0:
            content += ')' * parens_count
            
        # Ensure the script ends with a semicolon to avoid unterminated statement errors
        content = content.strip()
        if content and not content.endswith(';'):
            content += ';'
            
        # Wrap in try-catch with proper error handling
        wrapped_content = """
        try {
            %s
        } catch (e) {
            if (typeof console !== 'undefined' && console.error) {
                console.error('JS Error: ' + e.message);
            }
        }
        """ % content
        
        return wrapped_content
    
    def _find_script_elements(self, node) -> List:
        """
        Find all script elements in the document.
        
        Args:
            node: The node to search from
            
        Returns:
            List of script elements
        """
        result = []
        
        # Check if this is a script element
        if hasattr(node, 'tag_name') and node.tag_name.lower() == 'script':
            result.append(node)
        
        # Check children
        if hasattr(node, 'children'):
            for child in node.children:
                result.extend(self._find_script_elements(child))
                
        return result
    
    def handle_event(self, event_type: str, target_id: str = None, event_data: Dict[str, Any] = None) -> None:
        """
        Handle a DOM event.
        
        Args:
            event_type: Type of event (e.g., 'click', 'load')
            target_id: ID of the target element
            event_data: Additional event data
        """
        if not event_data:
            event_data = {}
            
        event_json = json.dumps(event_data)
        
        # Create and dispatch the event
        if target_id:
            js_code = f"""
            (function() {{
                var target = document.getElementById('{target_id}');
                if (target) {{
                    var event = new Event('{event_type}');
                    Object.assign(event, {event_json});
                    target.dispatchEvent(event);
                }}
            }})();
            """
        else:
            # Global event
            js_code = f"""
            (function() {{
                var event = new Event('{event_type}');
                Object.assign(event, {event_json});
                window.dispatchEvent(event);
            }})();
            """
            
        self.evaluate(js_code)
    
    def cleanup(self) -> None:
        """Clean up resources used by the JavaScript engine."""
        # Clear timers
        self.interpreter.evaljs("""
        for (var id in _timers) {
            clearTimeout(id);
            clearInterval(id);
        }
        """)
        
        # Clear console output
        self.console_output = []
        
        # Stop any running evaluation
        if self.eval_thread and self.eval_thread.is_alive():
            # Can't really stop a thread in Python, but mark it
            self.is_executing = False 