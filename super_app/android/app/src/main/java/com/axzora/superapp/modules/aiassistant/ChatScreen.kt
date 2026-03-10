// ChatScreen.kt - AI Assistant
package com.axzora.superapp.modules.aiassistant

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

data class ChatMessage(
    val id: String,
    val content: String,
    val isFromUser: Boolean,
    val timestamp: Long = System.currentTimeMillis()
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    onBack: () -> Unit
) {
    var messages by remember { 
        mutableStateOf(
            listOf(
                ChatMessage(
                    "1",
                    "Hello! I'm Mr. Happy, your AI Digital CEO at AXZORA. How can I help you today?",
                    isFromUser = false
                )
            )
        )
    }
    var inputText by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val listState = rememberLazyListState()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(36.dp)
                                .clip(RoundedCornerShape(18.dp))
                                .background(MaterialTheme.colorScheme.primary),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                Icons.Default.SmartToy,
                                contentDescription = null,
                                tint = Color.White
                            )
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text("Mr. Happy AI")
                            Text(
                                text = if (isLoading) "Typing..." else "Online",
                                style = MaterialTheme.typography.labelSmall,
                                color = if (isLoading) 
                                    MaterialTheme.colorScheme.primary 
                                else 
                                    Color(0xFF10B981)
                            )
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { /* Voice input */ }) {
                        Icon(Icons.Default.Mic, contentDescription = "Voice")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Messages List
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                state = listState,
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(messages) { message ->
                    MessageBubble(message = message)
                }
                
                if (isLoading) {
                    item {
                        Row(
                            modifier = Modifier.padding(start = 16.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(16.dp))
                                    .background(MaterialTheme.colorScheme.surfaceVariant)
                                    .padding(16.dp)
                            ) {
                                Row(
                                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    repeat(3) {
                                        Box(
                                            modifier = Modifier
                                                .size(8.dp)
                                                .clip(RoundedCornerShape(4.dp))
                                                .background(MaterialTheme.colorScheme.primary)
                                        )
                                        Spacer(modifier = Modifier.width(4.dp))
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // Quick Suggestions
            if (messages.size <= 2) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    QuickSuggestion("Book a flight") { inputText = it }
                    QuickSuggestion("Cricket scores") { inputText = it }
                    QuickSuggestion("Wallet balance") { inputText = it }
                }
                Spacer(modifier = Modifier.height(8.dp))
            }
            
            // Input Area
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                shape = RoundedCornerShape(24.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    TextField(
                        value = inputText,
                        onValueChange = { inputText = it },
                        modifier = Modifier.weight(1f),
                        placeholder = { Text("Ask Mr. Happy...") },
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                        keyboardActions = KeyboardActions(
                            onSend = {
                                if (inputText.isNotBlank()) {
                                    // Send message
                                    messages = messages + ChatMessage(
                                        id = System.currentTimeMillis().toString(),
                                        content = inputText,
                                        isFromUser = true
                                    )
                                    inputText = ""
                                    isLoading = true
                                    
                                    // Simulate AI response
                                    scope.launch {
                                        kotlinx.coroutines.delay(2000)
                                        messages = messages + ChatMessage(
                                            id = System.currentTimeMillis().toString(),
                                            content = getAIResponse(inputText),
                                            isFromUser = false
                                        )
                                        isLoading = false
                                    }
                                }
                            }
                        ),
                        colors = TextFieldDefaults.colors(
                            focusedContainerColor = Color.Transparent,
                            unfocusedContainerColor = Color.Transparent
                        )
                    )
                    
                    IconButton(
                        onClick = {
                            if (inputText.isNotBlank()) {
                                messages = messages + ChatMessage(
                                    id = System.currentTimeMillis().toString(),
                                    content = inputText,
                                    isFromUser = true
                                )
                                inputText = ""
                                isLoading = true
                                
                                scope.launch {
                                    kotlinx.coroutines.delay(2000)
                                    messages = messages + ChatMessage(
                                        id = System.currentTimeMillis().toString(),
                                        content = getAIResponse(inputText),
                                        isFromUser = false
                                    )
                                    isLoading = false
                                }
                            }
                        }
                    ) {
                        Icon(Icons.Default.Send, contentDescription = "Send")
                    }
                }
            }
        }
    }
}

@Composable
fun MessageBubble(message: ChatMessage) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (message.isFromUser) 
            Arrangement.End 
        else 
            Arrangement.Start
    ) {
        Box(
            modifier = Modifier
                .clip(
                    RoundedCornerShape(
                        topStart = 16.dp,
                        topEnd = 16.dp,
                        bottomStart = if (message.isFromUser) 16.dp else 4.dp,
                        bottomEnd = if (message.isFromUser) 4.dp else 16.dp
                    )
                )
                .background(
                    if (message.isFromUser) 
                        MaterialTheme.colorScheme.primary 
                    else 
                        MaterialTheme.colorScheme.surfaceVariant
                )
                .padding(12.dp)
        ) {
            Text(
                text = message.content,
                color = if (message.isFromUser) 
                    Color.White 
                else 
                    MaterialTheme.colorScheme.onSurface
            )
        }
    }
}

@Composable
fun QuickSuggestion(
    text: String,
    onClick: (String) -> Unit
) {
    SuggestionChip(
        onClick = { onClick(text) },
        label = { Text(text, style = MaterialTheme.typography.labelSmall) }
    )
}

fun getAIResponse(input: String): String {
    val lowerInput = input.lowercase()
    
    return when {
        lowerInput.contains("flight") -> {
            "I can help you book flights! Where would you like to travel from and to? I can find the best deals and even predict price trends for you."
        }
        lowerInput.contains("cricket") -> {
            "🏏 Live cricket updates! IND vs AUS is currently live at MCG. India is batting at 285/6. Would you like me to predict the match outcome?"
        }
        lowerInput.contains("wallet") || lowerInput.contains("balance") -> {
            "💰 Your wallet balance is ₹5,000. You also have 5 Happy Paisa (HP) which equals ₹5,000. Total: ₹10,000. Would you like to add money or make a transfer?"
        }
        lowerInput.contains("hotel") -> {
            "I can help you find and book hotels! Which city are you planning to visit? I'll find the best deals for you."
        }
        lowerInput.contains("hello") || lowerInput.contains("hi") -> {
            "Hello! 👋 I'm Mr. Happy, your AI assistant. I can help you with:\n\n✈️ Flight bookings\n🏨 Hotel reservations\n🏏 Cricket predictions\n💰 Wallet operations\n📱 Recharges\n\nWhat would you like to do today?"
        }
        else -> {
            "I understand you're asking about \"$input\". As your AI assistant, I can help you with flights, hotels, cricket, wallet operations, and more. Could you please be more specific about what you need?"
        }
    }
}

// Need to import this
import androidx.compose.foundation.lazy.rememberLazyListState
