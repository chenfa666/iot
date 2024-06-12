package com.example.lab_iot;

import android.content.Context;
import android.util.Log;
import org.eclipse.paho.android.service.MqttAndroidClient;
import org.eclipse.paho.client.mqttv3.DisconnectedBufferOptions;
import org.eclipse.paho.client.mqttv3.IMqttActionListener;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.IMqttToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import java.util.ArrayList;
import java.util.List;

public class MQTTHelper {
    public MqttAndroidClient mqttAndroidClient;
    private final String[] arrayTopics = {"chenfa666/feeds/temp", "chenfa666/feeds/humid", "chenfa666/feeds/state",
            "chenfa666/feeds/schedule", "chenfa666/feeds/command"};
    private final String clientId = "hehehehehe";
    private final String username = "chenfa666";
    private final String password = "";
    private final String serverUri = "tcp://io.adafruit.com:1883";
    private List<String> offlineDataList;

    public MQTTHelper(Context context) {
        mqttAndroidClient = new MqttAndroidClient(context, serverUri, clientId);
        offlineDataList = new ArrayList<>();

        mqttAndroidClient.setCallback(new MqttCallbackExtended() {
            @Override
            public void connectComplete(boolean b, String s) {
                Log.w("mqtt", s);
                // After successful connection, send offline data if any
                if (b) {
                    sendOfflineData();
                }
            }

            @Override
            public void connectionLost(Throwable throwable) {
                // Handle connection loss
            }

            @Override
            public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
                Log.w("Mqtt", mqttMessage.toString());
            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken iMqttDeliveryToken) {
                // Handle delivery completion
            }
        });

        connect();
    }

    public void setCallback(MqttCallbackExtended callback) {
        mqttAndroidClient.setCallback(callback);
    }

    private void connect() {
        MqttConnectOptions mqttConnectOptions = new MqttConnectOptions();
        mqttConnectOptions.setAutomaticReconnect(true);
        mqttConnectOptions.setCleanSession(false);
        mqttConnectOptions.setUserName(username);
        mqttConnectOptions.setPassword(password.toCharArray());

        try {
            mqttAndroidClient.connect(mqttConnectOptions, null, new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
                    DisconnectedBufferOptions disconnectedBufferOptions = new DisconnectedBufferOptions();
                    disconnectedBufferOptions.setBufferEnabled(true);
                    disconnectedBufferOptions.setBufferSize(100);
                    disconnectedBufferOptions.setPersistBuffer(false);
                    disconnectedBufferOptions.setDeleteOldestMessages(false);
                    mqttAndroidClient.setBufferOpts(disconnectedBufferOptions);
                    subscribeToTopic();
                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    Log.w("Mqtt", "Failed to connect to: " + serverUri + exception.toString());
                }
            });

        } catch (MqttException ex) {
            ex.printStackTrace();
        }
    }

    private void subscribeToTopic() {
        for (String arrayTopic : arrayTopics) {
            try {
                mqttAndroidClient.subscribe(arrayTopic, 0, null, new IMqttActionListener() {
                    @Override
                    public void onSuccess(IMqttToken asyncActionToken) {
                        Log.d("TEST", "Subscribed!");
                    }

                    @Override
                    public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                        Log.d("TEST", "Subscribed fail!");
                    }
                });

            } catch (MqttException ex) {
                System.err.println("Exceptionst subscribing");
                ex.printStackTrace();
            }
        }
    }

    public void sendMessage(String topic, String message) {
        if (mqttAndroidClient.isConnected()) {
            try {
                mqttAndroidClient.publish(topic, message.getBytes(), 0, false);
            } catch (MqttException e) {
                e.printStackTrace();
            }
        } else {
            storeOfflineData(topic, message);
        }
    }

    private void storeOfflineData(String topic, String message) {
        String offlineData = topic + "," + message;
        offlineDataList.add(offlineData);
    }

    private void sendOfflineData() {
        for (String data : offlineDataList) {
            String[] parts = data.split(",");
            String topic = parts[0];
            String message = parts[1];
            sendMessage(topic, message);
        }
        offlineDataList.clear();
    }

    public MqttAndroidClient getMqttAndroidClient() {
        return mqttAndroidClient;
    }
}
