// server side script called by GitHub Actions to periodically generate encodings from Coda
// setup: npm install node-fetch @tensorflow/tfjs-node@4.1.0 @tensorflow-models/universal-sentence-encoder
// usage: node questions-encodings.mjs ${CODA_TOKEN}
import * as tf from "@tensorflow/tfjs-node"; // do not remove import, `tf` is needed in following module even if not used in this file
import * as use from "@tensorflow-models/universal-sentence-encoder";
import fetch from "node-fetch";
import * as fs from "fs";
import { exit } from "process";

const filepath = "./";
const filename = filepath + "stampy-encodings.json";

let prevNumQs = 0;
if (fs.existsSync(filename)) {
  const p = JSON.parse(fs.readFileSync(filename, "utf8"));
  prevNumQs = p.numQs;
  console.log(`${prevNumQs} questions from in previous generated encodings.`);
}

if (process.argv.length < 3) {
  console.log(
    "ERROR: Missing required argument ${CODA_TOKEN}",
    "\nUSAGE: node questions-encodings.mjs ${CODA_TOKEN}"
  );
  exit(1);
}

const CODA_TOKEN = process.argv[2];
const CODA_DOC_ID = "fau7sl2hmG";
const table = "Answers";
const params =
  "useColumnNames=true&query=Status:%22Live%20on%20site%22&limit=1000";
const url = `https://coda.io/apis/v1/docs/${CODA_DOC_ID}/tables/${table}/rows?${params}`;

fetch(url, { headers: { Authorization: `Bearer ${CODA_TOKEN}` } })
.then((response) => response.json())
.then((r) => {

  const response = r.items;
  console.log(`${response.length} questions fetched from ${url}.`);

    const [questions, questionsNormalized, pageids] = [[], [], []];
    response.forEach((item) => {
        const names = item.values['All Phrasings'].split('\n').filter(Boolean);
        names.forEach((name) => {
            questions.push(name);
            questionsNormalized.push(name.toLowerCase());
            pageids.push(item.values["UI ID"]);
        });
    });

  const numQs = questions.length;

  use.load()
  .then((model) => {

    console.log(`Tensorflow's universal sentence encoder model loaded.`);
    model.embed(questionsNormalized)
    .then((enc) => enc.arraySync())
    .then((encodings) => {

      console.log("encodings", encodings)
      console.log(`Questions encoded.`);
      let data = JSON.stringify({ numQs, questions, pageids, encodings});
      fs.writeFile(filename, data, (err) => {
        if (err) {
          console.error(err);
        }
      });
      console.log(`Successfully saved answered questions & encodings from Coda to ${filename}.`);
    });
  });
});
