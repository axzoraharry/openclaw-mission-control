// LiveScoresScreen.kt
package com.axzora.superapp.modules.cricket

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

data class CricketMatch(
    val id: String,
    val team1: String,
    val team2: String,
    val score1: String,
    val score2: String,
    val status: String,
    val venue: String
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LiveScoresScreen(
    onBack: () -> Unit
) {
    // Sample matches
    val matches = remember {
        listOf(
            CricketMatch("1", "IND", "AUS", "285/6", "312/10", "LIVE - India batting", "MCG"),
            CricketMatch("2", "ENG", "SA", "245/10", "198/4", "LIVE - SA batting", "Lord's"),
            CricketMatch("3", "MI", "CSK", "180/5", "182/3", "CSK won by 5 wickets", "Wankhede")
        )
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Cricket Live") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { /* AI predictions */ }) {
                        Icon(Icons.Default.SmartToy, contentDescription = "AI Predictions")
                    }
                }
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // AI Prediction Banner
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    )
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Default.Psychology,
                            contentDescription = null,
                            modifier = Modifier.size(40.dp)
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                text = "AI Match Predictions",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.SemiBold
                            )
                            Text(
                                text = "Get AI-powered match predictions by Mr. Happy",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }
                }
            }
            
            // Matches
            items(matches) { match ->
                MatchCard(match = match)
            }
        }
    }
}

@Composable
fun MatchCard(match: CricketMatch) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            // Status
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = match.status,
                    style = MaterialTheme.typography.labelMedium,
                    color = if (match.status.contains("LIVE")) 
                        MaterialTheme.colorScheme.error 
                    else 
                        MaterialTheme.colorScheme.primary
                )
                Text(
                    text = match.venue,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                )
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Teams
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text(
                        text = match.team1,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = match.score1,
                        style = MaterialTheme.typography.bodyLarge
                    )
                }
                
                Text(
                    text = "vs",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                )
                
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        text = match.team2,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = match.score2,
                        style = MaterialTheme.typography.bodyLarge
                    )
                }
            }
        }
    }
}
