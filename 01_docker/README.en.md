# Let's containerize the wordsmith project!

The wordsmith project is split into 5 parts:

- web: frontend web server written in Go
- web2: a Node.js evolution of `web`, with the same core role but a more modern frontend and extra LLM-driven interactions
- words: REST API written in Java, to query the DB
- db: PostgreSQL database containing the words to display
- narrative (new): a Python Rest server that uses LLMs to generate a story

Our goal is to containerize this application.

There will be 3 steps:

1. Write multiple Dockerfiles. to build container images.
   1. run the containers independently
   2. connect them to the same server
2. Write a Compose file, to automate some the steps (connection)
   1. add volume to connect static files
   2. add a volume to persiste the database locally
   3. improve the Dockerfile of words for avoiding multiple rebuild with maven
3. Modify the app further
   1. use your creativity to improve the app

## Exercise 1: Dockerfiles

Our goal is to write Dockerfiles for the 3 containers.

First, `git clone` this repository. We need to create one
Dockerfile for each service. Pro tip: place each Dockerfile
in the corresponding directory (web, words, db).

The following paragraphs describe the installation instructions
for each service.

Note: in this first exercise, we only want to build the images
and check that they start correctly (`web` and `words` and `narrative` should display
a short message to indicate that they're running), but we're not
trying to run the whole application or to connect to the services.
This will come later.

### web (legacy, UI)

This is a web server written in Go. To compile Go code, we can
use the `golang` official image, or install Go packages in
any of the official base images.

The entire code is in a single
source file (`dispatcher.go`), and should be compiled like this:

```
go build dispatcher.go
```

This creates an executable named `dispatcher`, which should be
launched like this:

```
./dispatcher
Listening on port 80
```

The web server needs to access the `static` directory. This directory
must be a subdirectory of the current working directory when the
server is started.

Additional information:

- the server listens on port 80
- the Go compiler is only useful to build the server (not to run it)

### web2

This is the Node.js evolution of the original `web` service.
It keeps the same responsibility as `web`: serving the frontend
and proxying requests to backend services. The difference is that
it provides a newer UI and can call newer APIs such as the
`narrative` service to display LLM-generated content.

![preview](preview.png)


Additional information:

- the server listens on port 8000
- it serves static files from `public`
- it proxies `/words/*` requests to the Java `words` service
- it can also call the Python `narrative` service to show a generated story


### words

This is a REST API backend written in Java. It should be built with maven.

On a Debian or Ubuntu distribution, we can install Java and maven like this:

```
apt-get install maven openjdk-17-jdk
```

For the container image, a simple recommended base is:

```
maven:3.9.9-eclipse-temurin-17
```

To build the program, we can invoke maven like this:

```
mvn verify
```

The result is a file named `words.jar`, located in the `target` directory.

The server should be started by running the following command,
in the directory where `words.jar` is located:

```
java -Xmx64m -Xms64m -jar words.jar
```

Additional information:

- the server listens on port 8080
- compilation requires packages `maven` and `openjdk-17-jdk`
- execution requires package `openjdk-17-jdk` (`maven` is not necessary)

### db

This is a PostgreSQL database.

The database must be initialized with the schema (database and tables)
and the data (used by the application).

The file `words.sql` contains all the SQL commands necessary to create
the schema and load the data.

```
# cat words.sql
CREATE TABLE nouns (word TEXT NOT NULL);
CREATE TABLE verbs (word TEXT NOT NULL);
CREATE TABLE adjectives (word TEXT NOT NULL);
CREATE TABLE stories (
  story TEXT NOT NULL,
  model TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO nouns(word) VALUES
  ('cloud'),
  ('elephant'),
  ('gø language'),
  ('laptøp'),
  ('cøntainer'),
  ('micrø-service'),
  ('turtle'),
  ('whale'),
  ('gøpher'),
  ('møby døck'),
  ('server'),
  ('bicycle'),
  ('viking'),
  ('mermaid'),
  ('fjørd'),
  ('legø'),
  ('flødebolle'),
  ('smørrebrød');

INSERT INTO verbs(word) VALUES
  ('will drink'),
  ('smashes'),
  ('smøkes'),
  ('eats'),
  ('walks tøwards'),
  ('løves'),
  ('helps'),
  ('pushes'),
  ('debugs'),
  ('invites'),
  ('hides'),
  ('will ship');

INSERT INTO adjectives(word) VALUES
  ('the exquisite'),
  ('a pink'),
  ('the røtten'),
  ('a red'),
  ('the serverless'),
  ('a brøken'),
  ('a shiny'),
  ('the pretty'),
  ('the impressive'),
  ('an awesøme'),
  ('the famøus'),
  ('a gigantic'),
  ('the gløriøus'),
  ('the nørdic'),
  ('the welcøming'),
  ('the deliciøus');
```

Stories will be added at runtime by the model.

Additional information:

- we strongly suggest using the official PostgreSQL image that can
  be found on the Docker Hub (it's called `postgres`)
- if we check the [page of that official image](https://hub.docker.com/_/postgres) on the Docker Hub, we
  will find a lot of documentation; the section "Initialization scripts"
  is particularly useful to understand how to load `words.sql`
- it is advised to set up password authentication for the database; but in this case, to make our lives easier, we will simply authorize all connections (by setting environment variable `POSTGRES_HOST_AUTH_METHOD=trust`)
- to expose the database on local network and inspect, use port 5432

### narrative

This is a Python REST API that builds on top of the other services.
It calls the `words` API to fetch a set of generated words, then
uses an LLM exposed through Docker Model Runner to turn those words
into a short story.

The server should expose:

- `/healthz` to confirm that the service is running
- `/narrative` to generate a short story

When a story is generated, it is also stored in PostgreSQL together
with the model name and the creation date in the `stories` table.

Additional information:

- the server listens on port 8181
- it depends on `words` for vocabulary
- it depends on the Docker model server for text generation
- it writes generated stories to the `db` service

If you want to manually start and test a model before wiring it into
Compose, you can run:

```bash
docker model run ai/smollm2
```

Or preload it in the background:

```bash
docker model run --detach ai/smollm2
```

### Connect the containers

create a network

```docker network create inclass```

connect the containers one by one, for instance the db

```docker network connect inclass db```

Containers MUST have the following names to seamlesly connect, use --name <name>

- db
- words
- narrative


## Exercise 2: Compose file

When the 3 images build correctly, we can move on and write the Compose
file. We suggest placing the Compose file at the root of the repository.

At this point, we want to make sure that services can communicate
together, and that we can connect to `web`.

Note: the `web` service should be exposed.


### How Docker Model Runner Fits In Docker Compose

Docker Model Runner lets a service declare which model it needs directly
in `compose.yaml`. Compose then makes that model available to the service
at runtime, instead of forcing you to manage a separate inference container
by hand.

In practice, the workflow is:

- declare the model in the top-level `models` section
- attach that model to a service under `services.<name>.models`
- let the application call the model endpoint exposed by Docker Model Runner

Example:

```yaml
services:
  chat-app:
    image: my-chat-app
    models:
      - llm

models:
  llm:
    model: ai/smollm2
  
```

For this project, the `narrative` service uses that same pattern: it declares
an LLM model in Compose, then uses that model at runtime to turn the words
coming from the `words` API into a short story.

## Exercise 3: Play With Docker Model Server

- change the model with one more powerful (careful with memory)
- expand the database schema and save the protagonist
- try to link multiple stories
- immagination is your limit !
