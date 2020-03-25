// HSM display server - displays logs collected by the Host Spot Monitor
// Setup all required packages
'use strict';
var express = require("express");
var bodyParser = require("body-parser");
var fs = require("fs");
var jsdom = require("jsdom");
var readLine = require("readline");
var WebSocketServer = require("ws").Server;
var spawn = require("child_process").spawn;
var execSync = require("child_process").execSync;
// Read main html page - this will be parsed later
let mainPageContents = fs.readFileSync("./index.html");
// Read graphing html page - this will be parsed later
let graphPageContents = fs.readFileSync("./graph.html");
// Read realtime graphing html page - this will be parsed later
let realtimePageContents = fs.readFileSync("./realtime.html");
// Read log entry page - this will be reissued later
// create an express server to make a static file server
var app = express();
var statTime = [];
var relay = [];
var pipe_data = [];
var spawn = require('child_process').spawn;
var pipe = spawn('./flow_meter.py', []);
pipe.stdout.on('data', function(data) {
    pipe_data.push(data.toString());
});
pipe.stderr.on('data', function(data) {
	console.log("got an error");
	console.log(data.toString());
});
pipe.on('exit', function(error) {
        console.log("flow_meter terminated!");
	console.log(error);
});
// initialize global information

// check for changes to the test database every second
setInterval(function(){
    let changed = false;
    for (let entry of statTime) {
      changed |= fs.statSync(entry.Path).ctime.valueOf() != entry.Time.valueOf();
      entry.Time = fs.statSync(entry.Path).ctime;
    }
    if (changed) {
      console.log("need to do something");
    }
    let dataSent = false;
    for (let entry of relay) {
      for (let point of pipe_data) {
        entry.send("refresh " + point);
        dataSent = true;
      }
    }
    if (dataSent || ! relay.length) {
        pipe_data = [];
    }
  },5000);
// if the express server is contacted, look at the request and build a response or
// forward the request to the standard server behavior.
app.get("/", function(request, response, next) {
    // this is the main page so build replacement DOM
    // that has the sections available to edit
    let files = fs.readdirSync("./");
    let dom = new jsdom.JSDOM(mainPageContents);
    let document = dom.window.document;
    let insertionPoint = document.querySelector("#list");
    for (let file of files) {
      if (file.indexOf("plot_") == 0) {
        let element = document.createElement("a");
        let graphFile = file.replace("plot_", "graph_").replace(".js", ".html");
        element.setAttribute("href",graphFile);
        element.innerHTML = graphFile;
        let listElement = document.createElement("li");
        listElement.appendChild(element);
        insertionPoint.appendChild(listElement);
      }
    }
    insertionPoint = document.querySelector("#JSONlist");
    for (let file of files) {
      if (file.indexOf("plot_") == 0) {
        let element = document.createElement("a");
        element.setAttribute("href",file);
        element.innerHTML = file;
        let listElement = document.createElement("li");
        listElement.appendChild(element);
        insertionPoint.appendChild(listElement);
      }
    }
    response.send(dom.serialize());
  });
app.get("/graph_*", function(request, response, next) {
    console.log("process a graph route");
    let postScript = request.url.replace("/graph_","").replace(".html","") + ".js";
    let plotDataName = "plot_" + postScript;
    let dom = new jsdom.JSDOM(graphPageContents);
    let document = dom.window.document;
    let modificationPoint = document.querySelector("#title");
    modificationPoint.innerHTML = request.url;
    modificationPoint = document.querySelector("#dataTarget");
    modificationPoint.setAttribute("src", plotDataName);
    response.send(dom.serialize());
  });
app.get("/realtime.html", function(request, response, next) {
    console.log("process a realtime request route");
    let plotDataName = "realtime.js";
    let dom = new jsdom.JSDOM(realtimePageContents);
    let document = dom.window.document;
    let modificationPoint = document.querySelector("#dataTarget");
    modificationPoint.setAttribute("src", plotDataName);
    response.send(dom.serialize());
  });
app.get("*", function(request, response, next) {
    console.log("fell into default get");
    console.log(request.url);
    console.log(request.method);
    next();
  });
app.use(bodyParser.urlencoded({extended: true}));
app.post("/process_new_logs.html", function(request, response, next) {
    console.log("fell into process new logs");
    console.log(request.body);
    if (typeof request.body.yes === "undefined") {
        console.log("not doing post processing");
        response.redirect("/");
        return;
    }
    console.log("processing kernel logs");
    let date = new Date();
    let filePrefix = "plot_" + (date.getMonth()+1) + "-" + date.getDate() + "-" + (1900 + date.getYear());
    execSync("./process_iptable_logs.py /var/log/kern.log " + filePrefix);
    if (! (typeof request.body.box === "undefined")) {
        console.log("update the annotation database");
        execSync("./build_url_ip_db");
    }
    execSync("./annotate_plot_files")
    response.redirect("/");
    next();
  });
app.post("*", function(request, response, next) {
    console.log("fell into default post");
    console.log(request.url);
    console.log(request.method);
    next();
  });
app.use(express.static("./"));
var ws = new WebSocketServer({server: app.listen(process.env.PORT || 3000)});

ws.on("connection", function(connection) {
    relay.push(connection); // store for communication
    console.log("web socket connection made at server from HTML client page");
    connection.send("connected");
    connection.on("message", function (message) {
        if (message === "exit") {
          relay.splice(relay.indexOf(connection), 1);
          connection.close();
        }
      });
    connection.on("close", function(message) {
        relay.splice(relay.indexOf(connection), 1);
        connection.close();
        console.log("closing a connection");
      });
  });

console.log("HSM display server is listening");
