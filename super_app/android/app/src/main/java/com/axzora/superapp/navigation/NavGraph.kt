// NavGraph.kt - Navigation Graph
package com.axzora.superapp.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.axzora.superapp.modules.home.HomeScreen
import com.axzora.superapp.modules.flights.FlightSearchScreen
import com.axzora.superapp.modules.hotels.HotelSearchScreen
import com.axzora.superapp.modules.cricket.LiveScoresScreen
import com.axzora.superapp.modules.wallet.WalletHomeScreen
import com.axzora.superapp.modules.aiassistant.ChatScreen
import com.axzora.superapp.modules.profile.ProfileScreen

sealed class Screen(val route: String) {
    object Home : Screen("home")
    object Flights : Screen("flights")
    object Hotels : Screen("hotels")
    object Buses : Screen("buses")
    object Cricket : Screen("cricket")
    object Wallet : Screen("wallet")
    object Shopping : Screen("shopping")
    object Recharge : Screen("recharge")
    object AIAssistant : Screen("ai_assistant")
    object Profile : Screen("profile")
}

@Composable
fun AxzoraNavGraph(
    navController: NavHostController = rememberNavController(),
    startDestination: String = Screen.Home.route
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Screen.Home.route) {
            HomeScreen(
                onNavigate = { route -> navController.navigate(route) }
            )
        }
        
        composable(Screen.Flights.route) {
            FlightSearchScreen(
                onBack = { navController.popBackStack() }
            )
        }
        
        composable(Screen.Hotels.route) {
            HotelSearchScreen(
                onBack = { navController.popBackStack() }
            )
        }
        
        composable(Screen.Cricket.route) {
            LiveScoresScreen(
                onBack = { navController.popBackStack() }
            )
        }
        
        composable(Screen.Wallet.route) {
            WalletHomeScreen(
                onBack = { navController.popBackStack() }
            )
        }
        
        composable(Screen.AIAssistant.route) {
            ChatScreen(
                onBack = { navController.popBackStack() }
            )
        }
        
        composable(Screen.Profile.route) {
            ProfileScreen(
                onBack = { navController.popBackStack() }
            )
        }
    }
}
