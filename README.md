# Redomat -- Environment for reproducable building, integration, testing

To use Redomat to build a reference tposs, execute:

```
./build.sh <stage>
```
Setting the stage from which to start from is not a requirement.

Once the build is successful use

```
docker run --rm -ti -d -p <hostport>:80 <IMAGE> /build/serve.sh
```

to make the repositories accessible on `http://localhost:<hostport>`
