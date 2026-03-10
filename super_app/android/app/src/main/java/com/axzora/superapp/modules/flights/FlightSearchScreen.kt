// FlightSearchScreen.kt
package com.axzora.superapp.modules.flights

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FlightSearchScreen(
    onBack: () -> Unit
) {
    var fromCity by remember { mutableStateOf("") }
    var toCity by remember { mutableStateOf("") }
    var departureDate by remember { mutableStateOf("") }
    var passengers by remember { mutableStateOf(1) }
    var travelClass by remember { mutableStateOf("Economy") }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Search Flights") },
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
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // From/To Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    OutlinedTextField(
                        value = fromCity,
                        onValueChange = { fromCity = it },
                        label = { Text("From") },
                        leadingIcon = { Icon(Icons.Default.FlightTakeoff, null) },
                        modifier = Modifier.fillMaxWidth()
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    OutlinedTextField(
                        value = toCity,
                        onValueChange = { toCity = it },
                        label = { Text("To") },
                        leadingIcon = { Icon(Icons.Default.FlightLand, null) },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
            
            // Date Picker
            OutlinedTextField(
                value = departureDate,
                onValueChange = { departureDate = it },
                label = { Text("Departure Date") },
                leadingIcon = { Icon(Icons.Default.CalendarMonth, null) },
                modifier = Modifier.fillMaxWidth()
            )
            
            // Passengers & Class
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                OutlinedTextField(
                    value = passengers.toString(),
                    onValueChange = { passengers = it.toIntOrNull() ?: 1 },
                    label = { Text("Passengers") },
                    leadingIcon = { Icon(Icons.Default.Person, null) },
                    modifier = Modifier.weight(1f)
                )
                
                OutlinedTextField(
                    value = travelClass,
                    onValueChange = { travelClass = it },
                    label = { Text("Class") },
                    leadingIcon = { Icon(Icons.Default.Business, null) },
                    modifier = Modifier.weight(1f)
                )
            }
            
            // Search Button
            Button(
                onClick = { /* Search flights */ },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(16.dp)
            ) {
                Icon(Icons.Default.Search, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Search Flights", fontWeight = FontWeight.SemiBold)
            }
            
            // AI Assistance Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column {
                        Text(
                            text = "Need help finding flights?",
                            style = MaterialTheme.typography.titleMedium
                        )
                        Text(
                            text = "Ask Mr. Happy AI for personalized recommendations",
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                    Icon(
                        Icons.Default.SmartToy,
                        contentDescription = null,
                        modifier = Modifier.size(40.dp)
                    )
                }
            }
        }
    }
}
