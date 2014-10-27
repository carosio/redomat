#DockerBuilder

To use the DockerBuilder to build a reference tposs, execute:

```
./build.sh
```

Once the build is successful use:

```
docker run --rm -ti -d -p <hostport>:80 <IMAGE> /build/serve.sh
```

to make the repositories accessible on `http://localhost:<hostport>`
