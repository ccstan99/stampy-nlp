// server side script called by GitHub Actions to periodically generate encodings from Coda
// setup: npm install node-fetch @tensorflow/tfjs-node@4.1.0 @tensorflow-models/universal-sentence-encoder
// usage: node questions-encodings.mjs ${CODA_TOKEN}
import * as tf from "@tensorflow/tfjs-node"; // do not remove import, `tf` is needed in following module even if not used in this file
import * as use from "@tensorflow-models/universal-sentence-encoder";
import * as fs from "fs";
import fetch from "node-fetch";
import { exit } from "process";

if (process.argv.length < 3) {
  console.log(
    "ERROR: Missing required argument ${CODA_TOKEN}",
    "\nUSAGE: node questions-encodings.mjs ${CODA_TOKEN}"
  );
  exit(1);
}

const CODA_TOKEN = process.argv[2];
const CODA_DOC_ID = "fau7sl2hmG";
let table = "table-1Q8_MjxUes"; // On site table
let params =
  "useColumnNames=true&query=Status:%22Live%20on%20site%22&limit=1000";
let url = `https://coda.io/apis/v1/docs/${CODA_DOC_ID}/tables/${table}/rows?${params}`;

const byScore = (a, b) => b.score - a.score;
const normalize = (val) => val.toLowerCase();

let getCodaRows = async (url) => {
    const fetchItems = async (url) => {
        const response = await fetch(url, { headers: { Authorization: `Bearer ${CODA_TOKEN}` } });
        const data = await response.json();
        return {
            nextPage: data?.nextPageLink,
            items: data.items.map(item => ({
                name: item.name,
                pageid: item.values["UI ID"],
                alternates: item.values['Alternate Phrasings']
            }))
        };
    };

    let allItems = [];
    let more = null;
    do {
        const {items, nextPage} = await fetchItems(url);
        allItems = allItems.concat(items);
        more = nextPage;
    } while (Boolean(more))
    return allItems;
};

let embedItems = async (model, items) => {
    const [questions, questionsNormalized, pageids] = [[], [], []];
    items.forEach((item, index) => {
        questions.push(item.name);
        questionsNormalized.push(normalize(item.name));
        pageids.push(item.pageid);
        item.index = index;
    });

    return { encodings: await model.embed(questionsNormalized), questions, questionsNormalized, pageids };
};


let compareQuestions = async (items, model) => {
    const { encodings } = await embedItems(model, items);

    return async (mainQuestionId, alternative, n=5) => {
        const searchQuery = alternative.toLowerCase().trim().replace(/\s+/g, ' ');

        // encodings is 2D tensor of 512-dims embeddings for each sentence
        const top = await model.embed(searchQuery).then((encoding) => {
            // numerator of cosine similar is dot prod since vectors normalized
            const scores = tf.matMul(encoding, encodings, false, true).dataSync();

            // tensorflow requires explicit memory management to avoid memory leaks
            encoding.dispose();

            const questionsScored = items.map(({ name, pageid, index }) => ({
            name,
                pageid: pageid,
                score: scores[index],
            }));
            return questionsScored.sort(byScore).slice(0, n);
        });
        return top.some(({ pageid }) => pageid == mainQuestionId);
    };
};

let getAlternativePhrasings = async (items, isDuplicate) =>
    (await Promise.all(
        items.filter(question => Boolean(question.alternates))
            .map(({ pageid, name, alternates}) => alternates
                 .split('\n').
                 filter(q => q !== '' && q !== name)
                 .map(async alternate => ({pageid, name, alternate, duplicate: await isDuplicate(pageid, alternate)})))
            .flat()
    )).filter(({duplicate}) => !duplicate);


let processAllRows = async () => {
    const filepath = "./";
    const filename = filepath + "stampy-encodings.json";

    let prevNumQs = 0;
    if (fs.existsSync(filename)) {
        const p = JSON.parse(fs.readFileSync(filename, "utf8"));
        prevNumQs = p.numQs;
        console.log(`${prevNumQs} questions from in previous generated encodings.`);
    }

    let items = await getCodaRows(url);

    console.log(`${items.length} questions fetched from ${url}.`);

    const model = await use.load();
    console.log(`Tensorflow's universal sentence encoder model loaded.`);

    let isDuplicate = await compareQuestions(items, model);
    const alternativePhrasings = await getAlternativePhrasings(items, isDuplicate);
    let allItems = items.concat(alternativePhrasings);

    let { encodings, questions, pageids } = await embedItems(model, allItems);
    let encoded = await encodings.arraySync();

    console.log(`${allItems.length} questions encoded (${items.length} questions, ${alternativePhrasings.length} alternative phrasings).`);
    let data = JSON.stringify({ numQs: questions.length, questions, pageids, encoded});
    fs.writeFile(filename, data, (err) => {
        if (err) {
            console.error(err);
        }
    });
    console.log(`Successfully saved answered questions & encodings from Coda to ${filename}.`);
};

await processAllRows();
