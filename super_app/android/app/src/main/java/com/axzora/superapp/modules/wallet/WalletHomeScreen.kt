// WalletHomeScreen.kt
package com.axzora.superapp.modules.wallet

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.axzora.superapp.ui.theme.AxzoraPrimary
import com.axzora.superapp.ui.theme.AxzoraSecondary

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WalletHomeScreen(
    onBack: () -> Unit
) {
    var balance by remember { mutableStateOf(5000.0) }
    var hpBalance by remember { mutableStateOf(5.0) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Wallet") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            // Balance Card
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
                    .clip(RoundedCornerShape(20.dp))
                    .background(
                        Brush.linearGradient(
                            colors = listOf(AxzoraPrimary, AxzoraSecondary)
                        )
                    )
                    .padding(24.dp)
            ) {
                Column {
                    Text(
                        text = "Available Balance",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White.copy(alpha = 0.8f)
                    )
                    Text(
                        text = "₹${String.format("%,.0f", balance)}",
                        style = MaterialTheme.typography.headlineLarge,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Default.Star,
                            contentDescription = null,
                            tint = Color.Yellow,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "${hpBalance} Happy Paisa (HP)",
                            style = MaterialTheme.typography.titleMedium,
                            color = Color.White
                        )
                    }
                    Text(
                        text = "= ₹${String.format("%,.0f", hpBalance * 1000)}",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.White.copy(alpha = 0.7f)
                    )
                }
            }
            
            // Quick Actions
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                QuickActionButton(
                    icon = Icons.Default.Add,
                    label = "Add Money",
                    onClick = { },
                    modifier = Modifier.weight(1f)
                )
                QuickActionButton(
                    icon = Icons.Default.Send,
                    label = "Send",
                    onClick = { },
                    modifier = Modifier.weight(1f)
                )
                QuickActionButton(
                    icon = Icons.Default.QrCode,
                    label = "Scan QR",
                    onClick = { },
                    modifier = Modifier.weight(1f)
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // HP Converter
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = "Happy Paisa Converter",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(
                        text = "1 HP = ₹1,000 INR",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Button(
                            onClick = { /* Convert to HP */ },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("Convert to HP")
                        }
                        OutlinedButton(
                            onClick = { /* Convert to INR */ },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("Convert to INR")
                        }
                    }
                }
            }
            
            // Recent Transactions
            Text(
                text = "Recent Transactions",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(16.dp)
            )
            
            repeat(5) { index ->
                TransactionItem(
                    title = when (index % 5) {
                        0 -> "Flight Booking"
                        1 -> "Mobile Recharge"
                        2 -> "HP Earned"
                        3 -> "Hotel Booking"
                        else -> "Shopping"
                    },
                    amount = when (index % 5) {
                        0 -> -2500.0
                        1 -> -199.0
                        2 -> +0.5
                        3 -> -4500.0
                        else -> -899.0
                    },
                    isHP = index == 2
                )
            }
        }
    }
}

@Composable
fun QuickActionButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        onClick = onClick
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(icon, contentDescription = label)
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = label,
                style = MaterialTheme.typography.labelMedium
            )
        }
    }
}

@Composable
fun TransactionItem(
    title: String,
    amount: Double,
    isHP: Boolean = false
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    if (amount > 0) Icons.Default.ArrowDownward else Icons.Default.ArrowUpward,
                    contentDescription = null,
                    tint = if (amount > 0) Color(0xFF10B981) else Color(0xFFEF4444)
                )
                Spacer(modifier = Modifier.width(12.dp))
                Text(title)
            }
            
            Text(
                text = if (isHP) {
                    if (amount > 0) "+${amount} HP" else "${amount} HP"
                } else {
                    if (amount > 0) "+₹${String.format("%,.0f", amount)}" 
                    else "-₹${String.format("%,.0f", kotlin.math.abs(amount))}"
                },
                fontWeight = FontWeight.SemiBold,
                color = if (amount > 0) Color(0xFF10B981) else Color(0xFFEF4444)
            )
        }
    }
}
