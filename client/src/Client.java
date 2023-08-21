import java.io.IOException;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;

import java.net.Socket;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.nio.channels.SocketChannel;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Scanner;

import javax.swing.JFrame;

public class Client extends Thread {
    // Ports
    public static final int UDP_PORT = 1500;
    public static final int TCP_PORT = 1501;
    public static final int HEADER_LENGTH = 10;

    private static DatagramSocket socket = null;
    public static ArrayList<InetAddress> serversList = new ArrayList<InetAddress>();

    public static void broadcast(String broadcastMessage, InetAddress address) throws IOException {
        System.out.println("[Client]=>["+address+":"+UDP_PORT+"] Broadcasting UDP packet..");  
        // calling the constructor to create a datagram socket object 
        socket = new DatagramSocket();
        // Enabling the broadcast 
        socket.setBroadcast(true);

        // Putting the message in a packet
        byte[] buffer = broadcastMessage.getBytes();
        DatagramPacket packet = new DatagramPacket(buffer, buffer.length, address, UDP_PORT);

        // Send the packet in broadcast to each server listening to the UDP port 1500
        socket.send(packet);

        System.out.println("|_ [Client] The packet was sent successfully!\n");  
    }

    public static void connectTCP(InetAddress IPAddress) {
        final Socket clientSocket;
        final BufferedReader in;
        final PrintWriter out;
        final Scanner sc = new Scanner(System.in);
        try{
            clientSocket = new Socket(IPAddress, TCP_PORT);
            out = new PrintWriter(clientSocket.getOutputStream());
            in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));

            Thread sender = new Thread(new Runnable(){
                String msg;
                String name;
                boolean nameGiven=false;
                @Override
                public void run(){
                    while(true){
                        
                        while(!nameGiven){
                            msg = sc.nextLine();

                            if (msg.isEmpty()){
                                System.out.println("[Client] *You didn't enter an username*");
                                continue;
                            }

                            out.print(msg);
                            out.flush();
                            nameGiven=true;
                            name=msg;
                        }

                        msg = sc.nextLine();
                        out.print(name+" : "+msg);
                        out.flush();
                        msg="";
                    }
                }
            });
            sender.start();
            
            Thread receiver = new Thread(new Runnable(){
                String msg;
                @Override
                public void run(){
                    while(true){
                        try{
                            if((msg = in.readLine())!=null){
                                System.out.println("[Thiercelieux] "+msg);
                            }
                        }catch(IOException e){
                            e.printStackTrace();
                        }
                    }
                }
            });
            receiver.start();
        }
        catch(IOException e){
            e.printStackTrace();
        }
    }

    public static void udpListener() {
        try {
            // Define waiting time before stoping the loop
            long start = System.currentTimeMillis();
            long end = start + 1 * 1000;
            byte[] receiveData = new byte[50];
            byte[] sendData = new byte[50];
    
            while (true) { 
                // Get back the answer of the server
                DatagramPacket receivePacket = new DatagramPacket(receiveData, receiveData.length);
                socket.receive(receivePacket);
                
                // Converting that the client received in a string (UTF-8)
                String sentence = new String(receivePacket.getData(), "UTF-8");
                // Get the IP adress of the server who sent this message
                InetAddress IPAddress = receivePacket.getAddress();

                System.out.println("["+IPAddress+":"+UDP_PORT+"]=>[Client] '"+sentence+"'");

                // Check if it's a Werewolf server
                if (sentence.contains("I am a werewolf server")) {
                    serversList.add(IPAddress);
                    System.out.println("|_ [Client] Added "+IPAddress+":"+UDP_PORT+" to the servers list\n"); 
                }
                
                // After 1 second, stop waiting for answers from any servers 
                if (System.currentTimeMillis() < end) break;
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static void showServersList() { 
        int i = 0;
        // Print all avalaible werewolf servers
        for(InetAddress IPAddress : serversList) {
            System.out.println(" ["+i+"] "+IPAddress+":"+UDP_PORT);
            i++;
        }
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        // Broadcasting the message "Werewolf?"
        broadcast("Werewolf?", InetAddress.getByName("255.255.255.255"));
        Thread.sleep(1000);

        System.out.println("[Client] Waiting answers from servers..\n");
        Thread.sleep(1000);
        
        // Start the loop to listening UDP and know which server are werewolf game host
        udpListener();
        Thread.sleep(1000);
        System.out.println("[Client] Found "+serversList.size()+" server(s)\n"); 
        
        Thread.sleep(1000);
        System.out.println("Werewolf server(s) available");
        // Show avalaible compatible servers
        showServersList();

        // Wait the client to type on which server he want to connect
        System.out.println("\nIn order to connect to a server, enter his identifier (Represented by a number between brackets)");
        Scanner scanner = new Scanner(System.in);
        int chosenServerId = scanner.nextInt();

        // Try to connect in TCP to the  chosen server
        if (chosenServerId <= serversList.size()) {
            InetAddress IPAddress = serversList.get(chosenServerId);
            
            System.out.println("\n[Client]=>["+IPAddress+":"+TCP_PORT+"] Connecting to the server..");
            connectTCP(IPAddress);
        } else {
            System.out.println("\n[Client] This identifier doesn't exist!\n"); 
        }

    }
}