exports.postSymblCall = (ctx) => {
  let otSession = ctx.openTokSession;
  let token = otSession.generateToken();
  let meetingLinkURI = `http://${process.env.TUNNEL_DOMAIN}/join-call`;
  let symblProcessor = ctx.symblProcessor;
  let configOptions = ctx.request.body.config;
  let config = [];
  if (typeof configOptions == "string") {
    config.push(configOptions);
  }
  if (Array.isArray(configOptions)) {
    config.push(...configOptions);
  }
  symblProcessor.setConfig(config);

  return ctx.render("symbl-call", {
    apiKey: otSession.ot.apiKey,
    sessionId: otSession.sessionId,
    token: token,
    meetingLink: meetingLinkURI,
    config: config,
  });
};

exports.postSymblProcessing = async (ctx, next) => {
  let opentok = ctx.opentok;
  let opentokSession = ctx.openTokSession;
  let token = opentokSession.generateToken();
  let socketURI = `wss://${process.env.TUNNEL_DOMAIN}/socket`;
  let symblProcessor = ctx.symblProcessor;
  // let symblSdk = ctx.symblSdk;
  let websocket = ctx.ws;
  // let insightTypes = symblProcessor.setInsightTypes();
  // let handlers = symblProcessor.sethandlers();

  opentok.listStreams(opentokSession.sessionId, function (error, streams) {
    if (error) {
      console.log("Error:", error.message);
    } else {
      streams.forEach(async (stream) => {
        let stream_id = stream.id;
        let stream_name = stream.name;
        let symblConnection;
        let socketUriForStream = socketURI + "/" + stream_id;

        console.log("before ws.get");

        // send audio to python socket server instead of symbl
        // Make sure you have the WebSocket library imported
        const WebSocket = require("ws");

        websocket.get(`/socket/${stream_id}`, (ctx) => {
          // let connection = symblConnection;

          // Create a WebSocket connection to the Python server
          let pythonServerUri = `ws://localhost:8765/socket/${stream_id}`;
          console.log("pythonServerUri", pythonServerUri);

          let pythonServerSocket;

          try {
            pythonServerSocket = new WebSocket(pythonServerUri);

            // Handle the open event
            pythonServerSocket.on("open", () => {
              console.log("Connection to Python server established");
            });

            // Handle potential errors
            pythonServerSocket.on("error", (error) => {
              console.error("Error in WebSocket connection:", error);
            });
          } catch (e) {
            console.error(
              "Failed to create WebSocket connection to Python server:",
              e
            );
          }

          ctx.websocket.on("message", function (message) {
            try {
              const event = JSON.parse(message);
              if (event.event === "websocket:connected") {
                console.log(event);
              }
            } catch (err) {
              // console.log("about to check if pythonServerSocket is open");
              try {
                if (
                  pythonServerSocket &&
                  pythonServerSocket.readyState === WebSocket.OPEN
                ) {
                  console.log("sending message");
                  pythonServerSocket.send(message);
                } else {
                  // console.log(
                  //   "pythonServerSocket is not open or not available"
                  // );
                }
              } catch (e) {
                console.error("Failed to send message to Python server:", e);
              }
            }
          });

          // Handle the close event
          ctx.websocket.on("close", () => {
            if (pythonServerSocket) {
              pythonServerSocket.close();
            }
            console.log("WebSocket connection closed");
          });
        });

        opentok.websocketConnect(
          opentokSession.sessionId,
          token,
          socketUriForStream,
          { streams: [stream_id] },
          function (error, socket) {
            if (error) {
              console.log("Error:", error.message);
            } else {
              console.log("OpenTok Socket websocket connected");
            }
          }
        );
      });
    }
  });

  // TODO: 200 status set before complete, use promise.all()
  ctx.status = 200;
};

exports.getSymblTranscription = (ctx) => {
  let symblProcessor = ctx.symblProcessor;
  return ctx.render("symbl-transcriptions", {
    transcriptions: symblProcessor.getTranscriptions(),
  });
};

exports.getSymblActionItems = (ctx) => {
  let symblProcessor = ctx.symblProcessor;
  return ctx.render("symbl-output", {
    heading: "Action Items",
    list: symblProcessor.getActionItems(),
  });
};

exports.getSymblQuestions = (ctx) => {
  let symblProcessor = ctx.symblProcessor;
  return ctx.render("symbl-output", {
    heading: "Questions",
    list: symblProcessor.getQuestions(),
  });
};

exports.getSymblTopics = (ctx) => {
  let symblProcessor = ctx.symblProcessor;
  return ctx.render("symbl-output", {
    heading: "Topics",
    list: symblProcessor.getTopics(),
  });
};
