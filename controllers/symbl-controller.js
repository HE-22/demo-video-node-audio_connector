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
  let otSession = ctx.openTokSession;
  let token = otSession.generateToken();
  let socketURI = `wss://${process.env.TUNNEL_DOMAIN}/socket`;
  let symblProcessor = ctx.symblProcessor;
  let symblSdk = ctx.symblSdk;
  let ws = ctx.ws;
  let insightTypes = symblProcessor.setInsightTypes();
  let handlers = symblProcessor.sethandlers();

  opentok.listStreams(otSession.sessionId, function (error, streams) {
    if (error) {
      console.log("Error:", error.message);
    } else {
      streams.forEach(async (stream) => {
        let stream_id = stream.id;
        let stream_name = stream.name;
        let symblConnection;
        let socketUriForStream = socketURI + "/" + stream_id;

        console.log("connecting to symbl for: ", stream_id);
        try {
          symblConnection = await symblSdk.startRealtimeRequest({
            id: stream_id,
            speaker: {
              name: stream_name,
            },
            insightTypes: insightTypes,
            config: {
              meetingTitle: "My Test Meeting",
              confidenceThreshold: 0.9,
              timezoneOffset: 0, // Offset in minutes from UTC
              languageCode: "en-GB",
              sampleRateHertz: 16000,
            },
            handlers: handlers,
          });
          console.log("Connected to Symbl for: ", symblConnection);
        } catch (e) {
          console.log("Symbl connect error");
          console.error(e);
        }

        console.log("before ws.get");

        // send audio to python socket server instead of symbl
        // Make sure you have the WebSocket library imported
        const WebSocket = require("ws");

        ws.get(`/socket/${stream_id}`, (ctx) => {
          let connection = symblConnection;

          // Create a WebSocket connection to the Python server
          let pythonServerUri = `ws://localhost:8765/socket/${stream_id}`;
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
              console.log("about to check if pythonServerSocket is open");
              try {
                if (
                  pythonServerSocket &&
                  pythonServerSocket.readyState === WebSocket.OPEN
                ) {
                  pythonServerSocket.send(message);
                } else {
                  console.log(
                    "pythonServerSocket is not open or not available"
                  );
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
          otSession.sessionId,
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
