# EveContracts

## Installation

Before running, install Python dependencies with:
```bash
pip3 install -r requirements.txt
```

> [!NOTE]
> On macOS and Linux you may hit an error when installing mysqlclient:
> ```
> Collecting mysqlclient (from -r requirements.txt (line 8))
>   Using cached mysqlclient-2.2.7.tar.gz (91 kB)
>   Installing build dependencies ... done
>   Getting requirements to build wheel ... error
>   error: subprocess-exited-with-error
>
>   x Getting requirements to build wheel did not run successfully.
>   │ exit code: 1
>   ╰─> [35 lines of output]
>       /bin/sh: pkg-config: command not found
>       *********
>       Trying pkg-config --exists mysqlclient
>       Command 'pkg-config --exists mysqlclient' returned non-zero exit status 127.
> ```
>
> In that case install pkg-config: `sudo apt install pkg-config` or `brew install pkg-config`

> [!NOTE]
> On macOS and Linux you may hit an error when installing mysqlclient:
> ```
> Collecting mysqlclient (from -r requirements.txt (line 8))
>   Using cached mysqlclient-2.2.7.tar.gz (91 kB)
>   Installing build dependencies ... done
>   Getting requirements to build wheel ... error
>   error: subprocess-exited-with-error
>
>   × Getting requirements to build wheel did not run successfully.
>   │ exit code: 1
>   ╰─> [29 lines of output]
>       Trying pkg-config --exists mysqlclient
>       Command 'pkg-config --exists mysqlclient' returned non-zero exit status 1.
>       *********
>       Exception: Can not find valid pkg-config name.
>       Specify MYSQLCLIENT_CFLAGS and MYSQLCLIENT_LDFLAGS env vars manually
>       [end of output]
> ```
>
> In that case install libmysqlclient-dev: `sudo apt install libmysqlclient-dev` or `brew install libmysqlclient-dev`
>
> **libmysqlclient-dev** — is the package that provides the headers and libraries required to build applications that link against MySQL

To connect securely to MySQL, download the CA certificate to `~/.mysql/root.crt`
```
mkdir ~/.mysql
curl -o ~/.mysql/root.crt https://storage.yandexcloud.net/cloud-certs/CA.pem
```
