#!/bin/bash

INSTALLTO="/opt/rackspace"
INSTALLERURL='https://bftxmgmt-20200710.s3.us-west-2.amazonaws.com/splunk-linux-tgz-RAX.tgz'
INSTALLFILE="splunk-linux-tgz-RAX.tgz"
APPS_DIR="$INSTALLTO/splunkforwarder/etc/apps"
CONFIG_DIR="$APPS_DIR/txdir_deploymentclient/local"
MGMT_PORT_DIR="$INSTALLTO/splunkforwarder/etc/apps/txdir_mgmt_port"

# Splunk endpoint URL
SPLUNK_ENDPOINT="vpce-0b77d686cfa4ec333-xrgzidjy-us-gov-east-1a.vpce-svc-0d98c95a18f03f99b.us-gov-east-1.vpce.amazonaws.com"

# Creating structure
rm -Rf "$INSTALLTO" && mkdir -p "$INSTALLTO"
wget -O "/tmp/$INSTALLFILE" "$INSTALLERURL" && tar -zxf "/tmp/$INSTALLFILE" -C "$INSTALLTO"

# clear unneeded
rm -f "$INSTALLTO/splunkforwarder/etc/system/local/server.conf"

# adding dedicated user
useradd -d "$INSTALLTO" -r splunkrax
chown -R splunkrax:splunkrax "$INSTALLTO"

# Adjust global system settings to allow permissions
groupadd splunk

echo "rackspace - RAX" > "/etc/splunk"

# Creating deploymentclient.conf and outputs.conf
mkdir -p "$CONFIG_DIR"

printf "[deployment-client]\n[target-broker:deploymentServer]\ntargetUri = $SPLUNK_ENDPOINT:8089\n" > "$CONFIG_DIR/deploymentclient.conf"
echo "Created deploymentclient.conf"

printf "# BASE SETTINGS\n[tcpout]\ndefaultGroup = intermediate_forwarder\nforceTimebasedAutoLB = true\nforwardedindex.2.whitelist = (_audit|_introspection|_internal)\n[tcpout:intermediate_forwarder]\nserver = $SPLUNK_ENDPOINT:9997\n" > "$CONFIG_DIR/outputs.conf"
echo "Created outputs.conf"

# Set Local config
mkdir -p "$MGMT_PORT_DIR/local" "$MGMT_PORT_DIR/metadata"

printf "[install]\nstate = enabled\n[package]\ncheck_for_updates = false\n[ui]\nis_visible = false\nis_manageable = false\n" > "$MGMT_PORT_DIR/local/app.conf"
echo "Created app.conf"

printf "[settings]\nmgmtHostPort = 127.0.0.1:8085\n" > "$MGMT_PORT_DIR/local/web.conf"
echo "Created web.conf"

printf "[]\naccess = read : [ * ], write : [ admin ]\nexport = system\n" > "$MGMT_PORT_DIR/metadata/local.meta"
echo "Created local.meta"

# Set Permissions and service
chown -R splunkrax:splunkrax "$INSTALLTO"

"$INSTALLTO/splunkforwarder/bin/splunk" start --accept-license --answer-yes --no-prompt
"$INSTALLTO/splunkforwarder/bin/splunk" enable boot-start --accept-license --answer-yes --no-prompt

echo 'rackspace - RAX' > "/etc/splunk_config"
echo "Created splunk_config"