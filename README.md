# Redomat -- Environment for reproducable building, integration, testing

###DEPENDENCIES
* docker-py [github](https://github.com/docker/docker-py)
* docker [homepage](www.docker.com)
* python

###How to use
To use Redomat to build a reference tposs, execute:

```
python redomat.py <REDOMAT.XML>
```
Setting the stage from which to start from is not a requirement.

Once all stages are build you have the option to start building from a different stage, passing the stage to build from and the build-id:

```
python redomat.py -s <STAGE> <BUILS-ID> <REDOMAT.XML>
```

###How to serve build artifacts

To use the serve.sh script use this command:

```
docker run --rm -ti -d -p <hostport>:80 <IMAGE> /build/serve.sh
```

to make the repositories accessible on `http://localhost:<hostport>`

###REDOMAT.XML reference guide

####To declerate the Repo-tool xml in the Redomat.xml open up the section:
```
  <layer_declaration>
    REPO AND LAYER DECLERATION
  </layer_declaration>
```

In the layer declaration there are to knotes to declerate:
```
  <remote fetch="REPO_URL" name="REPO_NAME" />
  <layer path="BBLAYER_PATH" remote="REMOTE_NAME" revision="REPO_REVISION" reponame="REPO_URL" />
```

####To declerate build stages use:
```
  <buildstage id='STAGE_NAME'>
  <buildstage>
```

In this buildstage decleration there are three possible decleration:
```
  <prestage> STAGE_NAME </prestage>
  <dockerline> DOCKERFILE COMMAND </dockerline>
  <bitbake_target command="BITBAKE COMMAND"> BITBAKE_TARGET </bitbake_target> 
```

####to declerate local.conf:
```
  <local_conf>
  </local_conf>
```

```
  <BB_NUMBER_THREADS>NUMBER OF CPU CORES</BB_NUMBER_THREADS>
  <PARALLEL_MAKE>NUMBER OF MAKE THEADS</PARALLEL_MAKE>
  <MACHINE>MACHINE</MACHINE>
  <DISTRO>DISTRO</DISTRO>
```
