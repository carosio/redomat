# Redomat -- Environment for reproducable building, integration, testing

To use Redomat to build a reference tposs, execute:

```
./build.sh all
```

Once all stages are build you have the option to start building from a different stage, passing the stage to build from and the build-id:

```
./build.sh <STAGE> <BUILS-ID>
```

Use

```
docker run --rm -ti -d -p <hostport>:80 <IMAGE> /build/serve.sh
```

to make the repositories accessible on `http://localhost:<hostport>`
