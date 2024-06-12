package com.example.lab_iot;

import androidx.appcompat.app.AppCompatActivity;
import android.content.Context;
import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    MQTTHelper mqttHelper;
    TextView txtTemp, txtHumid, txtSchedule;
    EditText editTextTime;
    Button btnAddSchedule, btnRemoveSchedule;

    private List<String> offlineScheduleList;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        txtTemp = findViewById(R.id.txtTemperature);
        txtHumid = findViewById(R.id.txtHumidity);
        txtSchedule = findViewById(R.id.txtSchedule);
        editTextTime = findViewById(R.id.editTextTime);
        btnAddSchedule = findViewById(R.id.btnAddSchedule);
        btnRemoveSchedule = findViewById(R.id.btnRemoveSchedule);

        offlineScheduleList = new ArrayList<>();

        btnAddSchedule.setOnClickListener(v -> {
            String time = editTextTime.getText().toString();
            if (!time.isEmpty()) {
                if (isNetworkAvailable()) {
                    sendDataMQTT("chenfa666/feeds/command", "add " + time);
                } else {
                    storeOfflineData("add " + time);
                }
            }
        });

        btnRemoveSchedule.setOnClickListener(v -> {
            String time = editTextTime.getText().toString();
            if (!time.isEmpty()) {
                if (isNetworkAvailable()) {
                    sendDataMQTT("chenfa666/feeds/command", "remove " + time);
                } else {
                    storeOfflineData("remove " + time);
                }
            }
        });

        startMQTT();

        // Check for and send offline data when network becomes available
        sendOfflineDataIfAvailable();
    }

    private void sendOfflineDataIfAvailable() {
        if (isNetworkAvailable()) {
            List<String> offlineData = retrieveOfflineData();
            if (offlineData != null) {
                for (String data : offlineData) {
                    sendDataMQTT("chenfa666/feeds/command", data);
                }
                clearOfflineData();
            }
        }
    }

    public void sendDataMQTT(String topic, String value) {
        MqttMessage msg = new MqttMessage();
        msg.setId(1234);
        msg.setQos(0);
        msg.setRetained(false);

        byte[] b = value.getBytes(Charset.forName("UTF-8"));
        msg.setPayload(b);
        try {
            mqttHelper.mqttAndroidClient.publish(topic, msg);
        } catch (MqttException e) {
            Log.e("mqtt", "Error publishing message", e);
        }
    }

    public void startMQTT() {
        mqttHelper = new MQTTHelper(this);
        mqttHelper.setCallback(new MqttCallbackExtended() {
            @Override
            public void connectComplete(boolean reconnect, String serverURI) {
                Log.d("mqtt", "Connected to: " + serverURI);
            }

            @Override
            public void connectionLost(Throwable cause) {
                Log.d("mqtt", "Connection lost: " + cause.getMessage());
            }

            @Override
            public void messageArrived(String topic, MqttMessage message) throws Exception {
                Log.d("mqtt", topic + " : " + message.toString());
                if (topic.contains("temp")) {
                    txtTemp.setText(message.toString() + "°C");
                } else if (topic.contains("humid")) {
                    txtHumid.setText(message.toString() + "%");
                } else if (topic.contains("schedule")) {
                    txtSchedule.setText(message.toString());
                }
            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken token) {
                Log.d("mqtt", "Delivery complete");
            }
        });
    }

    private boolean isNetworkAvailable() {
        // Implement your network connectivity check logic here
        return true; // Dummy implementation, replace with actual logic
    }

    private void storeOfflineData(String data) {
        offlineScheduleList.add(data);
    }

    private List<String> retrieveOfflineData() {
        return offlineScheduleList;
    }

    private void clearOfflineData() {
        offlineScheduleList.clear();
    }
}
